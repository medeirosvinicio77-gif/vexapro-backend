import cv2
import os
import json
from datetime import datetime

class VideoPipeline:
    def __init__(self, video_path: str, project_id: str):
        self.video_path = video_path
        self.project_id = project_id
        self.output_dir = f"outputs/{project_id}"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/frames", exist_ok=True)
        
    def extract_frames(self, every_n_seconds: int = 1):
        """Extrai frames do vídeo a cada N segundos"""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        frame_interval = int(fps * every_n_seconds)
        frame_count = 0
        saved_count = 0
        frames_info = []
        
        print(f"📹 Processando vídeo: {duration:.1f}s, {fps:.0f} fps, {total_frames} frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                frame_path = f"{self.output_dir}/frames/frame_{saved_count:04d}.jpg"
                cv2.imwrite(frame_path, frame)
                
                timestamp = frame_count / fps if fps > 0 else 0
                frames_info.append({
                    "index": saved_count,
                    "frame_number": frame_count,
                    "timestamp": round(timestamp, 2),
                    "path": frame_path
                })
                saved_count += 1
                
            frame_count += 1
            
            # Progresso
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"⏳ Extraindo frames: {progress:.0f}%")
        
        cap.release()
        
        # Salvar metadados
        metadata = {
            "video_path": self.video_path,
            "duration": round(duration, 2),
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "extracted_frames": saved_count,
            "frame_interval_seconds": every_n_seconds,
            "processed_at": datetime.now().isoformat()
        }
        
        with open(f"{self.output_dir}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        with open(f"{self.output_dir}/frames_info.json", "w") as f:
            json.dump(frames_info, f, indent=2)
        
        print(f"✅ Extraídos {saved_count} frames")
        return metadata, frames_info
    
    def detect_aruco_markers(self, marker_size: float = 0.1):
        """Detecta marcadores ArUco nos frames extraídos"""
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        aruco_params = cv2.aruco.DetectorParameters()
        
        frames_dir = f"{self.output_dir}/frames"
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        all_detections = []
        
        for frame_file in frames:
            frame_path = os.path.join(frames_dir, frame_file)
            frame = cv2.imread(frame_path)
            
            if frame is None:
                continue
                
            corners, ids, rejected = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=aruco_params)
            
            if ids is not None:
                detection = {
                    "frame": frame_file,
                    "markers_found": len(ids),
                    "marker_ids": ids.flatten().tolist(),
                    "corners": [c.tolist() for c in corners]
                }
                all_detections.append(detection)
                
                # Desenhar marcadores no frame
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                marked_path = f"{self.output_dir}/frames/{frame_file.replace('.jpg', '_marked.jpg')}"
                cv2.imwrite(marked_path, frame)
        
        # Salvar detecções
        with open(f"{self.output_dir}/aruco_detections.json", "w") as f:
            json.dump(all_detections, f, indent=2)
        
        print(f"✅ Marcadores detectados em {len(all_detections)} frames")
        return all_detections
    
    def analyze_video_quality(self):
        """Analisa qualidade do vídeo"""
        frames_dir = f"{self.output_dir}/frames"
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg') and '_marked' not in f])
        
        if not frames:
            return {"error": "Nenhum frame encontrado"}
        
        total_brightness = 0
        total_contrast = 0
        
        for frame_file in frames[:10]:  # Analisar primeiros 10 frames
            frame_path = os.path.join(frames_dir, frame_file)
            frame = cv2.imread(frame_path)
            
            if frame is None:
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            total_brightness += gray.mean()
            total_contrast += gray.std()
        
        n = len(frames[:10])
        avg_brightness = total_brightness / n if n > 0 else 0
        avg_contrast = total_contrast / n if n > 0 else 0
        
        quality = {
            "average_brightness": round(avg_brightness, 1),
            "average_contrast": round(avg_contrast, 1),
            "brightness_status": "Boa" if 50 < avg_brightness < 200 else "Ruim",
            "contrast_status": "Boa" if avg_contrast > 30 else "Baixa",
            "recommendations": []
        }
        
        if avg_brightness < 50:
            quality["recommendations"].append("Ambiente muito escuro - grave com mais luz")
        if avg_brightness > 200:
            quality["recommendations"].append("Ambiente muito claro - evite luz direta")
        if avg_contrast < 30:
            quality["recommendations"].append("Baixo contraste - ambiente com pouca textura")
        
        with open(f"{self.output_dir}/quality.json", "w") as f:
            json.dump(quality, f, indent=2)
        
        print(f"✅ Qualidade analisada: Brilho={quality['average_brightness']}, Contraste={quality['average_contrast']}")
        return quality
    
    def run_full_pipeline(self):
        """Executa o pipeline completo"""
        print("=" * 50)
        print("🎬 Iniciando Pipeline VexaPro")
        print("=" * 50)
        
        # 1. Extrair frames
        print("\n📸 PASSO 1: Extraindo frames...")
        metadata, frames_info = self.extract_frames(every_n_seconds=1)
        
        # 2. Analisar qualidade
        print("\n🔍 PASSO 2: Analisando qualidade...")
        quality = self.analyze_video_quality()
        
        # 3. Detectar marcadores
        print("\n🎯 PASSO 3: Detectando marcadores ArUco...")
        detections = self.detect_aruco_markers()
        
        # Resumo
        result = {
            "project_id": self.project_id,
            "metadata": metadata,
            "quality": quality,
            "aruco_detections": {
                "total_frames_with_markers": len(detections),
                "markers_found": sum(d["markers_found"] for d in detections)
            },
            "output_dir": self.output_dir,
            "status": "completed"
        }
        
        with open(f"{self.output_dir}/pipeline_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print("\n" + "=" * 50)
        print("✅ PIPELINE CONCLUÍDO!")
        print(f"📁 Resultados salvos em: {self.output_dir}")
        print("=" * 50)
        
        return result