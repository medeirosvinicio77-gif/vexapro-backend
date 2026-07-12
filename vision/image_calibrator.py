"""
Calibrador de Imagem por Objeto de Referência
O usuário seleciona um objeto conhecido, informa a medida,
e o sistema calcula a escala para medir qualquer outro objeto
"""

import cv2
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional

class ImageCalibrator:
    def __init__(self):
        self.reference_points: List[Tuple[int, int]] = []
        self.reference_distance_pixels: float = 0
        self.reference_distance_meters: float = 0
        self.scale_factor: float = 0  # pixels por metro
        self.is_calibrated: bool = False
        
    def set_reference(self, point1: Tuple[int, int], point2: Tuple[int, int], distance_meters: float):
        """
        Define a referência de calibração
        
        Args:
            point1: (x1, y1) primeiro ponto
            point2: (x2, y2) segundo ponto
            distance_meters: distância real entre os pontos em metros
        """
        self.reference_points = [point1, point2]
        self.reference_distance_pixels = np.linalg.norm(
            np.array(point2) - np.array(point1)
        )
        self.reference_distance_meters = distance_meters
        self.scale_factor = self.reference_distance_pixels / distance_meters
        self.is_calibrated = True
        
        print(f"✅ Calibração definida:")
        print(f"   Pixels: {self.reference_distance_pixels:.1f}px")
        print(f"   Metros: {distance_meters:.3f}m")
        print(f"   Escala: {self.scale_factor:.1f} px/m")
    
    def measure_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> Dict:
        """
        Mede a distância entre dois pontos usando a calibração
        
        Returns:
            Dicionário com distância em pixels e metros
        """
        if not self.is_calibrated:
            return {"error": "Sistema não calibrado. Defina uma referência primeiro."}
        
        pixels = np.linalg.norm(np.array(point2) - np.array(point1))
        meters = pixels / self.scale_factor
        
        return {
            "distance_pixels": round(pixels, 1),
            "distance_meters": round(meters, 4),
            "distance_cm": round(meters * 100, 2),
            "distance_mm": round(meters * 1000, 1),
            "point1": list(point1),
            "point2": list(point2),
            "scale_factor": round(self.scale_factor, 1)
        }
    
    def measure_horizontal(self, y_level: int, x1: int, x2: int) -> Dict:
        """Mede distância horizontal em um nível Y"""
        return self.measure_distance((x1, y_level), (x2, y_level))
    
    def measure_vertical(self, x_level: int, y1: int, y2: int) -> Dict:
        """Mede distância vertical em um nível X"""
        return self.measure_distance((x_level, y1), (x_level, y2))
    
    def measure_rectangle(self, top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> Dict:
        """
        Mede um retângulo (como janela, porta, quadro)
        
        Returns:
            Largura, altura, diagonal e área
        """
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        width_px = abs(x2 - x1)
        height_px = abs(y2 - y1)
        
        width_m = width_px / self.scale_factor
        height_m = height_px / self.scale_factor
        diagonal_m = np.sqrt(width_m**2 + height_m**2)
        area_m2 = width_m * height_m
        
        return {
            "type": "rectangle",
            "width_pixels": round(width_px, 1),
            "height_pixels": round(height_px, 1),
            "width_meters": round(width_m, 4),
            "height_meters": round(height_m, 4),
            "width_cm": round(width_m * 100, 2),
            "height_cm": round(height_m * 100, 2),
            "diagonal_meters": round(diagonal_m, 4),
            "area_m2": round(area_m2, 4),
            "top_left": list(top_left),
            "bottom_right": list(bottom_right)
        }
    
    def measure_polygon(self, points: List[Tuple[int, int]]) -> Dict:
        """
        Mede perímetro e área de um polígono
        
        Args:
            points: Lista de pontos (x, y)
        """
        if len(points) < 3:
            return {"error": "Mínimo 3 pontos para um polígono"}
        
        # Perímetro
        perimeter_px = 0
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            perimeter_px += np.linalg.norm(np.array(p2) - np.array(p1))
        
        perimeter_m = perimeter_px / self.scale_factor
        
        # Área (fórmula de Shoelace)
        area_px = 0
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            area_px += x1 * y2 - x2 * y1
        area_px = abs(area_px) / 2
        area_m2 = area_px / (self.scale_factor ** 2)
        
        return {
            "type": "polygon",
            "vertices": len(points),
            "perimeter_meters": round(perimeter_m, 4),
            "area_m2": round(area_m2, 4),
            "area_cm2": round(area_m2 * 10000, 2),
            "points": [list(p) for p in points]
        }
    
    def draw_reference(self, image: np.ndarray) -> np.ndarray:
        """Desenha a linha de referência na imagem"""
        if len(self.reference_points) == 2:
            cv2.line(image, 
                    tuple(self.reference_points[0]), 
                    tuple(self.reference_points[1]), 
                    (0, 255, 0), 3)
            
            # Ponto médio para texto
            mid = tuple(np.mean(self.reference_points, axis=0).astype(int))
            cv2.circle(image, mid, 5, (0, 255, 0), -1)
            cv2.putText(image, f"{self.reference_distance_meters*100:.1f}cm", 
                       (mid[0] + 10, mid[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return image
    
    def draw_measurement(self, image: np.ndarray, point1: Tuple[int, int], 
                        point2: Tuple[int, int], color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
        """Desenha uma medição na imagem"""
        cv2.line(image, point1, point2, color, 2)
        
        # Círculos nos pontos
        cv2.circle(image, point1, 6, color, -1)
        cv2.circle(image, point2, 6, color, -1)
        
        # Texto com a medida
        measurement = self.measure_distance(point1, point2)
        if "error" not in measurement:
            mid = tuple(np.mean([point1, point2], axis=0).astype(int))
            cv2.putText(image, f"{measurement['distance_cm']}cm", 
                       (mid[0] + 10, mid[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return image
    
    def get_calibration_info(self) -> Dict:
        """Retorna informações da calibração atual"""
        if not self.is_calibrated:
            return {"calibrated": False}
        
        return {
            "calibrated": True,
            "reference_pixels": round(self.reference_distance_pixels, 1),
            "reference_meters": self.reference_distance_meters,
            "scale_factor_px_per_meter": round(self.scale_factor, 1),
            "scale_factor_px_per_cm": round(self.scale_factor / 100, 1),
            "reference_points": [list(p) for p in self.reference_points]
        }
    
    def save_image_with_measurements(self, image: np.ndarray, 
                                     measurements: List[Dict], 
                                     output_path: str) -> str:
        """Salva imagem com todas as medições desenhadas"""
        output = image.copy()
        
        # Desenhar referência
        output = self.draw_reference(output)
        
        # Desenhar medições
        colors = [
            (255, 0, 0),    # Vermelho
            (0, 0, 255),    # Azul
            (255, 165, 0),  # Laranja
            (128, 0, 128),  # Roxo
            (0, 128, 128),  # Verde água
        ]
        
        for i, m in enumerate(measurements):
            if "point1" in m and "point2" in m:
                color = colors[i % len(colors)]
                p1 = tuple(m["point1"])
                p2 = tuple(m["point2"])
                output = self.draw_measurement(output, p1, p2, color)
        
        # Adicionar legenda
        y_offset = 30
        cv2.putText(output, "=== VexaPro - Medicoes ===", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        y_offset += 30
        
        for i, m in enumerate(measurements):
            if "distance_cm" in m:
                cv2.putText(output, f"Medicao {i+1}: {m['distance_cm']}cm", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                y_offset += 25
        
        cv2.imwrite(output_path, output)
        return output_path


# Gerenciador global de calibrações por projeto
calibrations: Dict[str, ImageCalibrator] = {}

def get_calibrator(project_id: str) -> ImageCalibrator:
    """Obtém ou cria um calibrador para o projeto"""
    if project_id not in calibrations:
        calibrations[project_id] = ImageCalibrator()
    return calibrations[project_id]