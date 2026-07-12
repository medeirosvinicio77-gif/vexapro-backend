"""
Detector de Capacidades do Dispositivo
Identifica automaticamente os sensores disponíveis no celular
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class DeviceCategory(Enum):
    LIDAR = "lidar"           # iPhone Pro, iPad Pro (LiDAR)
    DEPTH_CAMERA = "depth"    # iPhone com Face ID, Android com ToF
    GYROSCOPE = "gyroscope"   # 99% dos smartphones
    BASIC = "basic"           # Celular simples, só câmera RGB

@dataclass
class DeviceInfo:
    category: DeviceCategory
    has_lidar: bool
    has_depth_camera: bool
    has_gyroscope: bool
    has_accelerometer: bool
    recommended_method: str
    accuracy_estimate: str
    tips: List[str]

class DeviceDetector:
    """Detecta e classifica o dispositivo do usuário"""
    
    # Tabela de dispositivos conhecidos
    KNOWN_DEVICES = {
        # iPhones com LiDAR
        "iPhone 12 Pro": DeviceCategory.LIDAR,
        "iPhone 13 Pro": DeviceCategory.LIDAR,
        "iPhone 14 Pro": DeviceCategory.LIDAR,
        "iPhone 15 Pro": DeviceCategory.LIDAR,
        "iPad Pro (2020)": DeviceCategory.LIDAR,
        "iPad Pro (2021)": DeviceCategory.LIDAR,
        "iPad Pro (2022)": DeviceCategory.LIDAR,
        
        # iPhones com Face ID (depth camera)
        "iPhone X": DeviceCategory.DEPTH_CAMERA,
        "iPhone XR": DeviceCategory.DEPTH_CAMERA,
        "iPhone XS": DeviceCategory.DEPTH_CAMERA,
        "iPhone 11": DeviceCategory.DEPTH_CAMERA,
        "iPhone 12": DeviceCategory.DEPTH_CAMERA,
        "iPhone 13": DeviceCategory.DEPTH_CAMERA,
        "iPhone 14": DeviceCategory.DEPTH_CAMERA,
        "iPhone 15": DeviceCategory.DEPTH_CAMERA,
        
        # Samsung com ToF
        "Galaxy S20": DeviceCategory.DEPTH_CAMERA,
        "Galaxy S21": DeviceCategory.DEPTH_CAMERA,
        "Galaxy Note 20": DeviceCategory.DEPTH_CAMERA,
    }
    
    @staticmethod
    def detect_from_user_agent(user_agent: str) -> Dict:
        """Detecta dispositivo a partir do User Agent"""
        info = {
            "has_lidar": False,
            "has_depth_camera": False,
            "has_gyroscope": True,  # Praticamente todos têm
            "has_accelerometer": True,
        }
        
        # Detectar iPhone
        if "iPhone" in user_agent:
            for device_name, category in DeviceDetector.KNOWN_DEVICES.items():
                if device_name in user_agent:
                    if category == DeviceCategory.LIDAR:
                        info["has_lidar"] = True
                        info["has_depth_camera"] = True
                    elif category == DeviceCategory.DEPTH_CAMERA:
                        info["has_depth_camera"] = True
                    break
        
        # Detectar Android com ToF
        if "Android" in user_agent:
            if any(device in user_agent for device in ["S20", "S21", "Note20"]):
                info["has_depth_camera"] = True
        
        return info
    
    @staticmethod
    def detect_from_metadata(metadata: Dict) -> Dict:
        """Detecta a partir dos metadados do vídeo"""
        info = {
            "has_lidar": False,
            "has_depth_camera": False,
            "has_gyroscope": True,
            "has_accelerometer": True,
        }
        
        # Verificar presença de dados de profundidade
        if metadata.get("has_depth_data"):
            info["has_depth_camera"] = True
        
        # Verificar resolução (LiDAR geralmente grava em 4K)
        if metadata.get("width", 0) >= 3840:
            info["has_lidar"] = True
        
        return info
    
    @staticmethod
    def classify_device(info: Dict) -> DeviceInfo:
        """Classifica o dispositivo em categorias"""
        
        if info.get("has_lidar"):
            category = DeviceCategory.LIDAR
            tips = [
                "✅ LiDAR detectado! Precisão de 1-2 cm",
                "Mantenha distância de 0.5 a 5 metros",
                "Evite superfícies muito escuras ou reflexivas"
            ]
            accuracy = "1-2 cm (Alta precisão)"
            method = "lidar_depth"
            
        elif info.get("has_depth_camera"):
            category = DeviceCategory.DEPTH_CAMERA
            tips = [
                "✅ Câmera de profundidade detectada",
                "Use em ambientes bem iluminados",
                "Coloque um objeto de referência para calibrar escala"
            ]
            accuracy = "2-5 cm (Boa precisão)"
            method = "depth_plus_reference"
            
        elif info.get("has_gyroscope"):
            category = DeviceCategory.GYROSCOPE
            tips = [
                "⚠️ Celular com giroscópio - use objeto de referência",
                "Coloque uma folha A4 ou régua visível na cena",
                "Movimentos lentos e estáveis",
                "Boa iluminação é essencial"
            ]
            accuracy = "3-10 cm (Precisão moderada)"
            method = "visual_reference"
            
        else:
            category = DeviceCategory.BASIC
            tips = [
                "⚠️ Celular básico - requer referência física",
                "Coloque uma régua ou objeto de tamanho conhecido",
                "Tire fotos de múltiplos ângulos",
                "Use boa iluminação"
            ]
            accuracy = "5-15 cm (Precisão básica)"
            method = "photo_reference"
        
        return DeviceInfo(
            category=category,
            has_lidar=info.get("has_lidar", False),
            has_depth_camera=info.get("has_depth_camera", False),
            has_gyroscope=info.get("has_gyroscope", True),
            has_accelerometer=info.get("has_accelerometer", True),
            recommended_method=method,
            accuracy_estimate=accuracy,
            tips=tips
        )