import numpy as np

class CameraCalibration:
    """Calibração padrão para smartphone"""
    
    @staticmethod
    def get_default_calibration(image_width: int = 1920, image_height: int = 1080):
        """Retorna uma calibração padrão estimada para smartphone"""
        focal_length = max(image_width, image_height) * 1.2
        
        camera_matrix = np.array([
            [focal_length, 0, image_width / 2],
            [0, focal_length, image_height / 2],
            [0, 0, 1]
        ], dtype=np.float64)
        
        dist_coeffs = np.zeros(5, dtype=np.float64)
        
        return camera_matrix, dist_coeffs
    
    @staticmethod
    def from_file(calib_path: str):
        """Carrega calibração de arquivo"""
        import json
        with open(calib_path, 'r') as f:
            data = json.load(f)
        camera_matrix = np.array(data["camera_matrix"], dtype=np.float64)
        dist_coeffs = np.array(data["dist_coeffs"], dtype=np.float64)
        return camera_matrix, dist_coeffs