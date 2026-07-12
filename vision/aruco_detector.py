import cv2
import numpy as np
import os
from typing import List, Dict, Optional, Tuple

class ArucoDetector:
    def __init__(self, marker_size_meters: float = 0.15):
        self.marker_size = marker_size_meters
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 23
        self.aruco_params.adaptiveThreshWinSizeStep = 10
        self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        
        # Criar o detector (OpenCV 4.7+)
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
    def detect_markers(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        if image is None:
            return None, None, None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
        return corners, ids, rejected
    
    def estimate_marker_positions(self, corners, ids, camera_matrix, dist_coeffs) -> List[Dict]:
        if ids is None or len(ids) == 0:
            return []
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners, self.marker_size, camera_matrix, dist_coeffs
        )
        marker_positions = []
        for i, marker_id in enumerate(ids.flatten()):
            tvec = tvecs[i][0]
            marker_positions.append({
                "id": int(marker_id),
                "position": {
                    "x": float(tvec[0]),
                    "y": float(tvec[1]),
                    "z": float(tvec[2])
                },
                "distance_to_camera": float(np.linalg.norm(tvec))
            })
        return marker_positions
    
    def calculate_distance(self, pos1: Dict, pos2: Dict) -> float:
        p1 = np.array([pos1["position"]["x"], pos1["position"]["y"], pos1["position"]["z"]])
        p2 = np.array([pos2["position"]["x"], pos2["position"]["y"], pos2["position"]["z"]])
        return float(np.linalg.norm(p2 - p1))
    
    def calculate_all_distances(self, marker_positions: List[Dict]) -> List[Dict]:
        distances = []
        n = len(marker_positions)
        for i in range(n):
            for j in range(i + 1, n):
                dist = self.calculate_distance(marker_positions[i], marker_positions[j])
                distances.append({
                    "marker_1": marker_positions[i]["id"],
                    "marker_2": marker_positions[j]["id"],
                    "distance_meters": round(dist, 4),
                    "position_1": marker_positions[i]["position"],
                    "position_2": marker_positions[j]["position"]
                })
        return distances
    
    def draw_markers(self, image: np.ndarray, corners, ids, marker_positions=None) -> np.ndarray:
        if ids is not None:
            image = cv2.aruco.drawDetectedMarkers(image, corners, ids)
        return image
    
    def process_frame(self, image_path: str, camera_matrix=None, dist_coeffs=None) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Não foi possível carregar a imagem"}
        
        if camera_matrix is None:
            h, w = image.shape[:2]
            focal = max(w, h)
            camera_matrix = np.array([[focal, 0, w/2], [0, focal, h/2], [0, 0, 1]], dtype=np.float64)
        
        if dist_coeffs is None:
            dist_coeffs = np.zeros(5, dtype=np.float64)
        
        corners, ids, _ = self.detect_markers(image)
        
        result = {
            "markers_detected": len(ids) if ids is not None else 0,
            "marker_ids": ids.flatten().tolist() if ids is not None else [],
            "has_markers": ids is not None and len(ids) > 0
        }
        
        if result["has_markers"]:
            positions = self.estimate_marker_positions(corners, ids, camera_matrix, dist_coeffs)
            result["positions"] = positions
            if len(positions) >= 2:
                result["distances"] = self.calculate_all_distances(positions)
        
        return result