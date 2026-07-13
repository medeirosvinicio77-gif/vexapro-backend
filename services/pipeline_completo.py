"""
Pipeline Completo de Análise de Ambiente
Extrai frames, detecta ArUco, calcula paredes e medidas reais
"""

import cv2
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class PipelineCompleto:
    def __init__(self, video_path: str, project_id: str, marker_size_meters: float = 0.15):
        self.video_path = video_path
        self.project_id = project_id
        self.marker_size = marker_size_meters
        self.output_dir = f"outputs/{project_id}"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/frames", exist_ok=True)
        
        # Configuração ArUco
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
    def extrair_frames(self, intervalo_segundos: float = 0.5) -> Dict:
        """Extrai frames do vídeo"""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        frame_interval = max(1, int(fps * intervalo_segundos))
        saved_count = 0
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_number % frame_interval == 0:
                frame_path = f"{self.output_dir}/frames/frame_{saved_count:04d}.jpg"
                cv2.imwrite(frame_path, frame)
                saved_count += 1
            frame_number += 1
        
        cap.release()
        
        metadata = {
            "duration": round(duration, 1),
            "fps": round(fps, 1),
            "width": width,
            "height": height,
            "total_frames": total_frames,
            "frames_extraidos": saved_count
        }
        
        with open(f"{self.output_dir}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ {saved_count} frames extraídos")
        return metadata
    
    def detectar_aruco_em_frames(self) -> List[Dict]:
        """Detecta ArUco em todos os frames e calcula posições 3D"""
        frames_dir = f"{self.output_dir}/frames"
        if not os.path.exists(frames_dir):
            return []
            
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        metadata_path = f"{self.output_dir}/metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                metadata = json.load(f)
        else:
            metadata = {"width": 1920, "height": 1080}
        
        w, h = metadata["width"], metadata["height"]
        focal = max(w, h) * 1.2
        camera_matrix = np.array([[focal, 0, w/2], [0, focal, h/2], [0, 0, 1]], dtype=np.float64)
        dist_coeffs = np.zeros(5, dtype=np.float64)
        
        todas_deteccoes = []
        
        for frame_file in frames:
            frame_path = os.path.join(frames_dir, frame_file)
            img = cv2.imread(frame_path)
            if img is None:
                continue
            
            corners, ids, _ = self.detector.detectMarkers(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
            
            if ids is not None and len(ids) >= 2:
                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                    corners, self.marker_size, camera_matrix, dist_coeffs
                )
                
                posicoes = {}
                for i, marker_id in enumerate(ids.flatten()):
                    tvec = tvecs[i][0]
                    posicoes[int(marker_id)] = {
                        "x": float(tvec[0]),
                        "y": float(tvec[1]),
                        "z": float(tvec[2])
                    }
                
                distancias = []
                ids_list = list(posicoes.keys())
                for i in range(len(ids_list)):
                    for j in range(i+1, len(ids_list)):
                        p1 = posicoes[ids_list[i]]
                        p2 = posicoes[ids_list[j]]
                        dist = np.sqrt((p2['x']-p1['x'])**2 + (p2['y']-p1['y'])**2 + (p2['z']-p1['z'])**2)
                        distancias.append({
                            "marcador_1": ids_list[i],
                            "marcador_2": ids_list[j],
                            "distancia_metros": round(dist, 4)
                        })
                
                todas_deteccoes.append({
                    "frame": frame_file,
                    "marcadores_encontrados": len(ids),
                    "posicoes": posicoes,
                    "distancias": distancias
                })
        
        with open(f"{self.output_dir}/aruco_deteccoes.json", "w") as f:
            json.dump(todas_deteccoes, f, indent=2)
        
        print(f"✅ ArUco detectado em {len(todas_deteccoes)} frames")
        return todas_deteccoes
    
    def reconstruir_paredes(self, deteccoes: List[Dict]) -> Dict:
        """Reconstrói as paredes a partir das detecções"""
        if not deteccoes:
            return self._planta_generica()
        
        todas_distancias = {}
        for det in deteccoes:
            for d in det.get("distancias", []):
                key = tuple(sorted([d["marcador_1"], d["marcador_2"]]))
                if key not in todas_distancias:
                    todas_distancias[key] = []
                todas_distancias[key].append(d["distancia_metros"])
        
        distancias_medias = {}
        for key, values in todas_distancias.items():
            distancias_medias[key] = round(sum(values) / len(values), 4)
        
        paredes = []
        for (m1, m2), dist in distancias_medias.items():
            paredes.append({
                "id": f"parede_{m1}_{m2}",
                "marcadores": [m1, m2],
                "comprimento_metros": dist,
                "comprimento_cm": round(dist * 100, 1)
            })
        
        paredes.sort(key=lambda p: p["comprimento_metros"], reverse=True)
        perimetro = sum(p["comprimento_metros"] for p in paredes)
        
        if len(paredes) >= 2:
            area = paredes[0]["comprimento_metros"] * paredes[1]["comprimento_metros"]
        else:
            area = 0
        
        resultado = {
            "tipo": "real",
            "total_paredes": len(paredes),
            "paredes": paredes,
            "perimetro_metros": round(perimetro, 2),
            "area_m2": round(area, 2),
            "altura_estimada": 2.60,
            "confianca": "alta" if len(paredes) >= 4 else "media"
        }
        
        with open(f"{self.output_dir}/paredes.json", "w") as f:
            json.dump(resultado, f, indent=2)
        
        return resultado
    
    def _planta_generica(self) -> Dict:
        return {
            "tipo": "generica",
            "total_paredes": 4,
            "paredes": [
                {"id": "parede_1", "comprimento_metros": 4.0, "comprimento_cm": 400},
                {"id": "parede_2", "comprimento_metros": 3.0, "comprimento_cm": 300},
                {"id": "parede_3", "comprimento_metros": 4.0, "comprimento_cm": 400},
                {"id": "parede_4", "comprimento_metros": 3.0, "comprimento_cm": 300},
            ],
            "perimetro_metros": 14.0,
            "area_m2": 12.0,
            "altura_estimada": 2.60,
            "confianca": "baixa",
            "aviso": "Nenhum marcador ArUco detectado. Use marcadores para medição precisa."
        }
    
    def executar(self) -> Dict:
        print("=" * 60)
        print("🏗️ PIPELINE COMPLETO VEXAPRO")
        print("=" * 60)
        
        print("\n📸 PASSO 1: Extraindo frames...")
        metadata = self.extrair_frames()
        
        print("\n🎯 PASSO 2: Detectando ArUco...")
        deteccoes = self.detectar_aruco_em_frames()
        
        print("\n🧱 PASSO 3: Reconstruindo paredes...")
        paredes = self.reconstruir_paredes(deteccoes)
        
        resultado = {
            "project_id": self.project_id,
            "metadata": metadata,
            "paredes": paredes,
            "total_frames_processados": metadata["frames_extraidos"],
            "frames_com_aruco": len(deteccoes),
            "processado_em": datetime.now().isoformat()
        }
        
        with open(f"{self.output_dir}/resultado_final.json", "w") as f:
            json.dump(resultado, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE CONCLUÍDO!")
        print(f"   Paredes: {paredes['total_paredes']}")
        print(f"   Perímetro: {paredes['perimetro_metros']}m")
        print(f"   Área: {paredes['area_m2']}m²")
        print("=" * 60)
        
        return resultado