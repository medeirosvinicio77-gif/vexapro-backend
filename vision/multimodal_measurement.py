"""
Sistema de Medição Multimodal
Mede objetos de diferentes formas dependendo do dispositivo
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class MeasurementMethod(Enum):
    ARUCO = "aruco"                    # Marcadores ArUco
    LIDAR_DEPTH = "lidar_depth"        # LiDAR do iPhone Pro
    DEPTH_REFERENCE = "depth_reference" # Câmera de profundidade + referência
    VISUAL_REFERENCE = "visual_reference" # Objeto de referência visual
    PHOTO_REFERENCE = "photo_reference"   # Foto com régua/objeto conhecido
    MANUAL = "manual"                   # Medição manual informada

@dataclass
class Measurement:
    type: str          # "window_width", "door_height", "wall_length", etc.
    value_meters: float
    method: MeasurementMethod
    confidence: float  # 0 a 1
    reference_used: Optional[str] = None

class MultimodalMeasurement:
    """Sistema principal de medição"""
    
    # Objetos comuns com tamanhos conhecidos
    REFERENCE_OBJECTS = {
        "credit_card": {"width": 0.0856, "height": 0.0540, "unit": "m"},
        "a4_paper": {"width": 0.210, "height": 0.297, "unit": "m"},
        "ruler_30cm": {"length": 0.30, "unit": "m"},
        "door_standard": {"width": 0.80, "height": 2.10, "unit": "m"},
        "tile_30cm": {"size": 0.30, "unit": "m"},
        "brick": {"length": 0.19, "height": 0.09, "unit": "m"},
        "iphone_14": {"width": 0.0715, "height": 0.1467, "unit": "m"},
    }
    
    def __init__(self, device_info: Dict):
        self.device_info = device_info
        self.measurements: List[Measurement] = []
        
    def measure_with_aruco(self, image: np.ndarray, aruco_detector, camera_matrix, dist_coeffs) -> List[Measurement]:
        """Medição usando marcadores ArUco"""
        corners, ids, _ = aruco_detector.detect_markers(image)
        
        if ids is None or len(ids) < 2:
            return []
        
        positions = aruco_detector.estimate_marker_positions(corners, ids, camera_matrix, dist_coeffs)
        measurements = []
        
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dist = aruco_detector.calculate_distance(positions[i], positions[j])
                measurements.append(Measurement(
                    type=f"distance_marker_{positions[i]['id']}_to_{positions[j]['id']}",
                    value_meters=round(dist, 4),
                    method=MeasurementMethod.ARUCO,
                    confidence=0.95,
                    reference_used=f"ArUco markers {positions[i]['id']} and {positions[j]['id']}"
                ))
        
        return measurements
    
    def measure_with_reference_object(self, image: np.ndarray, reference_type: str) -> Optional[Measurement]:
        """
        Mede usando um objeto de referência conhecido
        Detecta o objeto na imagem e usa como escala
        """
        if reference_type not in self.REFERENCE_OBJECTS:
            return None
        
        ref = self.REFERENCE_OBJECTS[reference_type]
        
        # Converter para HSV para detectar objetos
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar bordas
        edges = cv2.Canny(gray, 50, 150)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Pegar o maior contorno (provavelmente o objeto de referência)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Calcular pixels por metro
        if "width" in ref:
            pixels_per_meter = w / ref["width"]
        elif "length" in ref:
            pixels_per_meter = max(w, h) / ref["length"]
        else:
            pixels_per_meter = w / ref.get("size", 0.30)
        
        # Usar essa escala para medir outros objetos na cena
        # (implementação simplificada)
        
        return Measurement(
            type="reference_scale",
            value_meters=ref.get("width", ref.get("length", 0.30)),
            method=MeasurementMethod.VISUAL_REFERENCE,
            confidence=0.70,
            reference_used=reference_type
        )
    
    def measure_window_or_door(self, image: np.ndarray, object_type: str, 
                                reference_measurement: Optional[Measurement] = None) -> Optional[Measurement]:
        """
        Mede uma janela ou porta usando detecção de bordas + escala de referência
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        
        # Dilatar para conectar bordas próximas
        kernel = np.ones((5,5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Filtrar contornos retangulares grandes
        rectangles = []
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:  # Retângulo
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Janelas são mais largas, portas são mais altas
                if object_type == "window" and 0.5 < aspect_ratio < 2.5:
                    rectangles.append((x, y, w, h))
                elif object_type == "door" and 0.3 < aspect_ratio < 0.8:
                    rectangles.append((x, y, w, h))
        
        if not rectangles:
            return None
        
        # Pegar o maior retângulo
        largest = max(rectangles, key=lambda r: r[2] * r[3])
        x, y, w, h = largest
        
        # Se temos uma medida de referência, calcular escala
        if reference_measurement:
            # Usar a referência para calcular pixels por metro
            # (simplificado - em produção seria mais complexo)
            pixels_per_meter = 1000  # valor estimado
            
            if object_type == "window":
                width_meters = w / pixels_per_meter
                return Measurement(
                    type="window_width",
                    value_meters=round(width_meters, 3),
                    method=MeasurementMethod.VISUAL_REFERENCE,
                    confidence=0.65,
                    reference_used=reference_measurement.reference_used
                )
            elif object_type == "door":
                height_meters = h / pixels_per_meter
                return Measurement(
                    type="door_height",
                    value_meters=round(height_meters, 3),
                    method=MeasurementMethod.VISUAL_REFERENCE,
                    confidence=0.65,
                    reference_used=reference_measurement.reference_used
                )
        
        return None
    
    def get_recommended_method(self) -> Dict:
        """Retorna o método recomendado baseado no dispositivo"""
        methods = {
            "lidar": {
                "name": "LiDAR (iPhone Pro)",
                "accuracy": "1-2 cm",
                "setup": "Apenas aponte e meça",
                "requires_marker": False
            },
            "depth_camera": {
                "name": "Câmera de Profundidade",
                "accuracy": "2-5 cm",
                "setup": "Use um cartão de crédito como referência",
                "requires_marker": False
            },
            "gyroscope": {
                "name": "Giroscópio + Referência Visual",
                "accuracy": "3-10 cm",
                "setup": "Coloque uma folha A4 ou régua na cena",
                "requires_marker": True
            },
            "basic": {
                "name": "Referência Manual",
                "accuracy": "5-15 cm",
                "setup": "Meça um objeto com trena e informe o valor",
                "requires_marker": True
            }
        }
        
        return methods.get(self.device_info.get("recommended_method", "basic"), methods["basic"])