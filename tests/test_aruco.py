import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np

def test_create_detector():
    """Testa criação do detector"""
    from vision.aruco_detector import ArucoDetector
    detector = ArucoDetector(marker_size_meters=0.15)
    assert detector is not None
    assert detector.marker_size == 0.15

def test_detect_no_markers():
    """Testa detecção em imagem vazia"""
    from vision.aruco_detector import ArucoDetector
    detector = ArucoDetector()
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    corners, ids, rejected = detector.detect_markers(img)
    assert ids is None or len(ids) == 0

def test_calculate_distance():
    """Testa cálculo de distância"""
    from vision.aruco_detector import ArucoDetector
    detector = ArucoDetector()
    pos1 = {"position": {"x": 0, "y": 0, "z": 0}}
    pos2 = {"position": {"x": 1, "y": 0, "z": 0}}
    dist = detector.calculate_distance(pos1, pos2)
    assert abs(dist - 1.0) < 0.001

def test_calculate_multiple_distances():
    """Testa cálculo de distâncias entre 3 marcadores"""
    from vision.aruco_detector import ArucoDetector
    detector = ArucoDetector()
    positions = [
        {"id": 0, "position": {"x": 0, "y": 0, "z": 0}},
        {"id": 1, "position": {"x": 1, "y": 0, "z": 0}},
        {"id": 2, "position": {"x": 0, "y": 1, "z": 0}},
    ]
    distances = detector.calculate_all_distances(positions)
    assert len(distances) == 3

def test_device_detector():
    """Testa detector de dispositivo"""
    from vision.device_detector import DeviceDetector
    info = DeviceDetector.detect_from_user_agent(
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
    )
    assert "has_gyroscope" in info

def test_multimodal_measurement():
    """Testa medição multimodal"""
    from vision.multimodal_measurement import MultimodalMeasurement
    mm = MultimodalMeasurement({"has_gyroscope": True})
    recommendation = mm.get_recommended_method()
    assert "accuracy" in recommendation

def test_camera_calibration():
    """Testa calibração de câmera"""
    from vision.camera_calibration import CameraCalibration
    mtx, dist = CameraCalibration.get_default_calibration(1920, 1080)
    assert mtx.shape == (3, 3)
    assert dist.shape == (5,)

def test_point_cloud_generator():
    """Testa gerador de nuvem de pontos"""
    from vision.point_cloud import PointCloudGenerator
    gen = PointCloudGenerator("test_project")
    assert gen.project_id == "test_project"