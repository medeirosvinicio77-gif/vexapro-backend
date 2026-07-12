from fastapi import APIRouter, Form, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
import json
import numpy as np
from vision.device_detector import DeviceDetector
from vision.multimodal_measurement import MultimodalMeasurement
from vision.aruco_detector import ArucoDetector
from vision.floor_plan import FloorPlanGenerator
from vision.image_calibrator import ImageCalibrator, get_calibrator
import cv2

router = APIRouter(prefix="/measurements", tags=["measurements"])

# ============ Modelos Pydantic ============

class CalibrationData(BaseModel):
    project_id: str
    point1_x: int
    point1_y: int
    point2_x: int
    point2_y: int
    distance_meters: float

class MeasurementData(BaseModel):
    project_id: str
    point1_x: int
    point1_y: int
    point2_x: int
    point2_y: int

class RectangleData(BaseModel):
    project_id: str
    x1: int
    y1: int
    x2: int
    y2: int

class PolygonData(BaseModel):
    project_id: str
    points: list  # Lista de [x, y]

# ============ Endpoints de Dispositivo ============

@router.post("/detect-device")
async def detect_device(user_agent: str = Form(None)):
    """Detecta as capacidades do dispositivo"""
    info = DeviceDetector.detect_from_user_agent(user_agent or "")
    device = DeviceDetector.classify_device(info)
    
    measurement = MultimodalMeasurement(info)
    recommendation = measurement.get_recommended_method()
    
    return {
        "device_info": {
            "category": device.category.value,
            "has_lidar": device.has_lidar,
            "has_depth_camera": device.has_depth_camera,
            "has_gyroscope": device.has_gyroscope,
            "accuracy": device.accuracy_estimate
        },
        "recommended_method": recommendation,
        "tips": device.tips
    }

# ============ Endpoints de Medição de Objetos ============

@router.post("/measure-object")
async def measure_object(
    image: UploadFile = File(...),
    object_type: str = Form(...),
    reference_type: str = Form(None),
    known_measurement: float = Form(None),
    project_id: str = Form(...)
):
    """Mede um objeto na imagem"""
    temp_path = f"temp_measurement.jpg"
    with open(temp_path, "wb") as f:
        f.write(await image.read())
    
    img = cv2.imread(temp_path)
    
    if img is None:
        return {"error": "Não foi possível carregar a imagem"}
    
    device_info = {"has_gyroscope": True}
    measurer = MultimodalMeasurement(device_info)
    
    results = []
    
    if reference_type:
        ref_measurement = measurer.measure_with_reference_object(img, reference_type)
        if ref_measurement:
            results.append({
                "type": "reference_scale",
                "value": ref_measurement.value_meters,
                "method": ref_measurement.method.value,
                "confidence": ref_measurement.confidence
            })
            
            target = measurer.measure_window_or_door(img, object_type, ref_measurement)
            if target:
                results.append({
                    "type": target.type,
                    "value": target.value_meters,
                    "method": target.method.value,
                    "confidence": target.confidence
                })
    
    if known_measurement:
        results.append({
            "type": object_type,
            "value": known_measurement,
            "method": "manual",
            "confidence": 1.0,
            "note": "Medida informada manualmente"
        })
    
    detector = ArucoDetector()
    corners, ids, _ = detector.detect_markers(img)
    
    if ids is not None and len(ids) >= 2:
        h, w = img.shape[:2]
        camera_matrix = np.array([[w, 0, w/2], [0, w, h/2], [0, 0, 1]])
        dist_coeffs = np.zeros(5)
        
        aruco_measurements = measurer.measure_with_aruco(img, detector, camera_matrix, dist_coeffs)
        for m in aruco_measurements:
            results.append({
                "type": m.type,
                "value": m.value_meters,
                "method": m.method.value,
                "confidence": m.confidence
            })
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return {
        "object_type": object_type,
        "project_id": project_id,
        "measurements": results,
        "count": len(results)
    }

@router.get("/reference-objects")
async def list_reference_objects():
    """Lista objetos que podem ser usados como referência"""
    return {
        "reference_objects": [
            {"name": "Cartão de crédito", "id": "credit_card", "size": "8.56 x 5.40 cm"},
            {"name": "Folha A4", "id": "a4_paper", "size": "21.0 x 29.7 cm"},
            {"name": "Régua 30cm", "id": "ruler_30cm", "size": "30 cm"},
            {"name": "Porta padrão", "id": "door_standard", "size": "80 x 210 cm"},
            {"name": "Azulejo 30cm", "id": "tile_30cm", "size": "30 x 30 cm"},
            {"name": "Tijolo", "id": "brick", "size": "19 x 9 cm"},
            {"name": "iPhone 14", "id": "iphone_14", "size": "7.15 x 14.67 cm"}
        ]
    }

# ============ Endpoints de Calibração por Imagem ============

@router.post("/calibrate")
async def calibrate_image(data: CalibrationData):
    """
    Calibra a imagem usando um objeto de referência.
    O usuário clica em 2 pontos e informa a distância real entre eles.
    """
    calibrator = get_calibrator(data.project_id)
    calibrator.set_reference(
        (data.point1_x, data.point1_y),
        (data.point2_x, data.point2_y),
        data.distance_meters
    )
    
    return {
        "status": "calibrated",
        "message": f"Calibração definida com sucesso! Escala: {calibrator.scale_factor:.1f} px/m",
        "calibration": calibrator.get_calibration_info()
    }

@router.post("/measure-distance")
async def measure_distance(data: MeasurementData):
    """
    Mede a distância entre dois pontos na imagem.
    Requer calibração prévia.
    """
    calibrator = get_calibrator(data.project_id)
    
    if not calibrator.is_calibrated:
        return {"error": "Calibre a imagem primeiro! Use POST /calibrate"}
    
    result = calibrator.measure_distance(
        (data.point1_x, data.point1_y),
        (data.point2_x, data.point2_y)
    )
    
    return result

@router.post("/measure-rectangle")
async def measure_rectangle(data: RectangleData):
    """
    Mede um retângulo (janela, porta, quadro, etc).
    Requer calibração prévia.
    """
    calibrator = get_calibrator(data.project_id)
    
    if not calibrator.is_calibrated:
        return {"error": "Calibre a imagem primeiro! Use POST /calibrate"}
    
    result = calibrator.measure_rectangle(
        (data.x1, data.y1),
        (data.x2, data.y2)
    )
    
    return result

@router.post("/measure-polygon")
async def measure_polygon(data: PolygonData):
    """
    Mede perímetro e área de um polígono.
    Requer calibração prévia.
    """
    calibrator = get_calibrator(data.project_id)
    
    if not calibrator.is_calibrated:
        return {"error": "Calibre a imagem primeiro! Use POST /calibrate"}
    
    points = [tuple(p) for p in data.points]
    result = calibrator.measure_polygon(points)
    
    return result

@router.get("/calibration-info/{project_id}")
async def get_calibration_info(project_id: str):
    """Retorna informações da calibração atual do projeto"""
    calibrator = get_calibrator(project_id)
    return calibrator.get_calibration_info()

@router.post("/reset-calibration/{project_id}")
async def reset_calibration(project_id: str):
    """Reseta a calibração do projeto"""
    from vision.image_calibrator import calibrations
    if project_id in calibrations:
        del calibrations[project_id]
    return {"status": "reset", "message": "Calibração removida"}

# ============ Endpoints de Planta Baixa ============

@router.post("/floor-plan/{project_id}")
async def generate_floor_plan(
    project_id: str,
    width: float = Form(None),
    height: float = Form(None),
    openings: str = Form(None)
):
    """Gera planta baixa do projeto"""
    generator = FloorPlanGenerator(project_id)
    
    if width and height:
        openings_list = json.loads(openings) if openings else []
        result = generator.generate_simple_floor_plan(width, height, openings_list)
        return result
    
    frames_dir = f"outputs/{project_id}/frames"
    if os.path.exists(frames_dir):
        result = generator.generate_from_frames(frames_dir)
        if "error" not in result:
            return result
    
    cloud_path = f"outputs/{project_id}/pointcloud/cloud.json"
    if os.path.exists(cloud_path):
        with open(cloud_path, "r") as f:
            cloud_data = json.load(f)
        points = np.array(cloud_data["points"])
        result = generator.generate_from_points(points)
        return result
    
    return {"error": "Sem dados para gerar planta baixa. Envie um vídeo primeiro."}

@router.get("/floor-plan/{project_id}/image")
async def get_floor_plan_image(project_id: str):
    """Retorna a imagem da planta baixa"""
    image_path = f"outputs/{project_id}/floorplan/floor_plan.png"
    if os.path.exists(image_path):
        return FileResponse(image_path, media_type="image/png")
    return {"error": "Planta baixa não encontrada"}

@router.get("/floor-plan/{project_id}/data")
async def get_floor_plan_data(project_id: str):
    """Retorna os dados da planta baixa em JSON"""
    json_path = f"outputs/{project_id}/floorplan/floor_plan.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    return {"error": "Planta baixa não encontrada"}