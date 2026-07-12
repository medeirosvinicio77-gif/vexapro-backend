"""
Gerador de Planta Baixa 2D a partir da nuvem de pontos 3D
"""

import cv2
import numpy as np
import json
import os
from typing import List, Tuple, Optional, Dict

class FloorPlanGenerator:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.output_dir = f"outputs/{project_id}"
        os.makedirs(f"{self.output_dir}/floorplan", exist_ok=True)
        
    def project_to_floor(self, points_3d: np.ndarray, grid_size: float = 0.05) -> np.ndarray:
        """
        Projeta pontos 3D para o plano do chão (XY)
        Cria uma grade 2D de ocupação
        
        Args:
            points_3d: Array Nx3 com coordenadas (x, y, z)
            grid_size: Tamanho da célula em metros
        
        Returns:
            Matriz 2D com densidade de pontos por célula
        """
        if len(points_3d) == 0:
            return np.zeros((100, 100))
        
        # Filtrar pontos próximos ao chão (z entre 0 e 0.5m)
        floor_mask = (points_3d[:, 1] >= 0) & (points_3d[:, 1] <= 0.5)
        floor_points = points_3d[floor_mask]
        
        if len(floor_points) == 0:
            floor_points = points_3d
        
        # Coordenadas X e Z (planta baixa é vista de cima)
        x = floor_points[:, 0]
        z = floor_points[:, 2]
        
        # Definir limites
        x_min, x_max = x.min() - 1, x.max() + 1
        z_min, z_max = z.min() - 1, z.max() + 1
        
        # Criar grade
        cols = int((x_max - x_min) / grid_size) + 1
        rows = int((z_max - z_min) / grid_size) + 1
        
        grid = np.zeros((rows, cols), dtype=np.float32)
        
        # Preencher grade
        for px, pz in zip(x, z):
            col = int((px - x_min) / grid_size)
            row = int((pz - z_min) / grid_size)
            if 0 <= row < rows and 0 <= col < cols:
                grid[row, col] += 1
        
        # Normalizar
        if grid.max() > 0:
            grid = grid / grid.max()
        
        return grid
    
    def detect_walls_from_grid(self, grid: np.ndarray, threshold: float = 0.1) -> List[Dict]:
        """
        Detecta paredes a partir da grade de ocupação
        
        Returns:
            Lista de paredes com coordenadas (x1, y1, x2, y2)
        """
        # Binarizar
        binary = (grid > threshold).astype(np.uint8) * 255
        
        # Encontrar contornos
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        walls = []
        
        for contour in contours:
            # Aproximar contorno com polígono
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Extrair linhas (paredes)
            for i in range(len(approx)):
                pt1 = approx[i][0]
                pt2 = approx[(i + 1) % len(approx)][0]
                
                walls.append({
                    "x1": float(pt1[0]),
                    "y1": float(pt1[1]),
                    "x2": float(pt2[0]),
                    "y2": float(pt2[1]),
                    "length_pixels": float(np.linalg.norm(pt2 - pt1))
                })
        
        return walls
    
    def draw_floor_plan(self, grid: np.ndarray, walls: List[Dict], 
                        scale_pixels_per_meter: float = 100) -> np.ndarray:
        """
        Desenha a planta baixa como imagem
        
        Args:
            grid: Grade de ocupação
            walls: Lista de paredes
            scale_pixels_per_meter: Escala para desenho
        
        Returns:
            Imagem da planta baixa
        """
        # Criar canvas branco
        h, w = grid.shape
        img_h = int(h * scale_pixels_per_meter / 10)
        img_w = int(w * scale_pixels_per_meter / 10)
        
        canvas = np.ones((max(img_h, 400), max(img_w, 600), 3), dtype=np.uint8) * 255
        
        # Desenhar grade de ocupação como fundo
        grid_resized = cv2.resize(grid, (canvas.shape[1], canvas.shape[0]))
        grid_colored = (grid_resized * 255).astype(np.uint8)
        grid_colored = cv2.cvtColor(grid_colored, cv2.COLOR_GRAY2BGR)
        
        # Azul claro para áreas ocupadas
        mask = grid_resized > 0.1
        canvas[mask] = [240, 240, 255]
        
        # Desenhar paredes
        for wall in walls:
            pt1 = (int(wall["x1"] * scale_pixels_per_meter / 10), 
                   int(wall["y1"] * scale_pixels_per_meter / 10))
            pt2 = (int(wall["x2"] * scale_pixels_per_meter / 10), 
                   int(wall["y2"] * scale_pixels_per_meter / 10))
            
            cv2.line(canvas, pt1, pt2, (0, 0, 0), 3)
        
        # Adicionar informações
        cv2.putText(canvas, f"Planta Baixa - Projeto: {self.project_id}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(canvas, f"Escala aproximada: 1:{int(scale_pixels_per_meter/10)}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        # Salvar
        output_path = f"{self.output_dir}/floorplan/floor_plan.png"
        cv2.imwrite(output_path, canvas)
        
        return canvas
    
    def generate_from_points(self, points_3d: np.ndarray, 
                            scale_pixels_per_meter: float = 100) -> Dict:
        """
        Gera planta baixa completa a partir de pontos 3D
        
        Returns:
            Dicionário com resultados
        """
        print(f"🏗️ Gerando planta baixa com {len(points_3d)} pontos...")
        
        # Projetar para o chão
        grid = self.project_to_floor(points_3d, grid_size=0.05)
        
        # Detectar paredes
        walls = self.detect_walls_from_grid(grid)
        print(f"🧱 {len(walls)} paredes detectadas")
        
        # Calcular dimensões aproximadas
        if len(points_3d) > 0:
            x_span = points_3d[:, 0].max() - points_3d[:, 0].min()
            z_span = points_3d[:, 2].max() - points_3d[:, 2].min()
            area_approx = x_span * z_span
        else:
            x_span = z_span = area_approx = 0
        
        # Desenhar planta
        image = self.draw_floor_plan(grid, walls, scale_pixels_per_meter)
        
        # Salvar dados
        result = {
            "project_id": self.project_id,
            "dimensions": {
                "width_meters": round(x_span, 2),
                "depth_meters": round(z_span, 2),
                "area_sqm": round(area_approx, 2)
            },
            "walls_count": len(walls),
            "walls": walls,
            "image_path": f"{self.output_dir}/floorplan/floor_plan.png",
            "scale": f"1:{int(scale_pixels_per_meter/10)}"
        }
        
        with open(f"{self.output_dir}/floorplan/floor_plan.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Planta baixa salva: {result['image_path']}")
        print(f"📐 Dimensões: {result['dimensions']['width_meters']}m x {result['dimensions']['depth_meters']}m")
        print(f"📏 Área aproximada: {result['dimensions']['area_sqm']}m²")
        
        return result
    
    def generate_from_frames(self, frames_dir: str) -> Dict:
        """
        Gera planta baixa a partir de frames com ArUco
        """
        from vision.aruco_detector import ArucoDetector
        from vision.camera_calibration import CameraCalibration
        
        detector = ArucoDetector(marker_size_meters=0.15)
        camera_matrix, dist_coeffs = CameraCalibration.get_default_calibration()
        
        all_points = []
        
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        print(f"📸 Processando {len(frames)} frames...")
        
        for frame_file in frames:
            frame_path = os.path.join(frames_dir, frame_file)
            result = detector.process_frame(frame_path, camera_matrix, dist_coeffs)
            
            if result.get("has_markers") and "positions" in result:
                for pos in result["positions"]:
                    p = pos["position"]
                    all_points.append([p["x"], p["y"], p["z"]])
        
        if len(all_points) == 0:
            print("❌ Nenhum marcador ArUco detectado")
            return {"error": "Nenhum marcador detectado"}
        
        points_array = np.array(all_points)
        return self.generate_from_points(points_array)
    
    def generate_simple_floor_plan(self, width: float, height: float, 
                                   openings: List[Dict] = None) -> Dict:
        """
        Gera uma planta baixa simples com dimensões conhecidas
        
        Args:
            width: Largura em metros
            height: Altura (profundidade) em metros
            openings: Lista de aberturas (portas, janelas)
        """
        # Criar canvas
        scale = 50  # pixels por metro
        margin = 50
        
        img_w = int(width * scale) + margin * 2
        img_h = int(height * scale) + margin * 2
        
        canvas = np.ones((img_h, img_w, 3), dtype=np.uint8) * 255
        
        # Desenhar paredes externas
        x1, y1 = margin, margin
        x2, y2 = margin + int(width * scale), margin + int(height * scale)
        
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 3)
        
        # Preencher interior
        canvas[y1+3:y2-3, x1+3:x2-3] = [245, 245, 255]
        
        # Desenhar aberturas
        if openings:
            for opening in openings:
                ox = margin + int(opening.get("x", 0) * scale)
                oy = margin + int(opening.get("y", 0) * scale)
                ow = int(opening.get("width", 0.8) * scale)
                
                if opening.get("type") == "door":
                    cv2.rectangle(canvas, (ox, oy), (ox + ow, oy + 5), (255, 255, 255), -1)
                    cv2.rectangle(canvas, (ox, oy), (ox + ow, oy + 5), (0, 200, 0), 2)
                    cv2.putText(canvas, "PORTA", (ox, oy - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 1)
                elif opening.get("type") == "window":
                    cv2.rectangle(canvas, (ox, oy - 2), (ox + ow, oy + 7), (255, 255, 255), -1)
                    cv2.rectangle(canvas, (ox, oy - 2), (ox + ow, oy + 7), (200, 100, 0), 2)
                    cv2.putText(canvas, "JANELA", (ox, oy - 12), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 100, 0), 1)
        
        # Adicionar medidas
        cv2.putText(canvas, f"{width:.2f}m", 
                   (x1 + int(width * scale / 2) - 30, y1 - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(canvas, f"{height:.2f}m", 
                   (x2 + 10, y1 + int(height * scale / 2)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Área
        cv2.putText(canvas, f"Area: {width * height:.2f} m²", 
                   (x1 + int(width * scale / 2) - 50, y2 + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        # Salvar
        output_path = f"{self.output_dir}/floorplan/floor_plan.png"
        cv2.imwrite(output_path, canvas)
        
        result = {
            "project_id": self.project_id,
            "dimensions": {
                "width_meters": width,
                "depth_meters": height,
                "area_sqm": round(width * height, 2)
            },
            "walls": [
                {"side": "front", "length": width},
                {"side": "right", "length": height},
                {"side": "back", "length": width},
                {"side": "left", "length": height}
            ],
            "openings": openings or [],
            "image_path": output_path
        }
        
        with open(f"{self.output_dir}/floorplan/floor_plan.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Planta baixa gerada: {output_path}")
        
        return result