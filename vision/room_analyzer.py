"""
Analisador Inteligente de Ambientes
Detecta janelas, portas, tomadas, pontos hidráulicos e classifica cômodos
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class RoomType(Enum):
    KITCHEN = "cozinha"
    BATHROOM = "banheiro"
    LIVING_ROOM = "sala"
    BEDROOM = "quarto"
    LAUNDRY = "lavanderia"
    HALLWAY = "corredor"
    BALCONY = "varanda"
    OFFICE = "escritorio"

class OpeningType(Enum):
    DOOR = "porta"
    WINDOW = "janela"
    SLIDING_DOOR = "porta_correr"
    BALCONY_DOOR = "porta_varanda"

class InfrastructureType(Enum):
    OUTLET = "tomada"
    SWITCH = "interruptor"
    LIGHT_POINT = "ponto_luz"
    WATER_POINT = "ponto_agua"
    DRAIN = "ralo"
    GAS_POINT = "ponto_gas"

@dataclass
class DetectedOpening:
    type: OpeningType
    x: int
    y: int
    width: int
    height: int
    confidence: float
    dimensions_cm: Optional[Dict] = None

@dataclass
class DetectedInfrastructure:
    type: InfrastructureType
    x: int
    y: int
    confidence: float
    subtype: Optional[str] = None  # ex: "2P+T", "simples", "agua_fria"

@dataclass
class RoomAnalysis:
    room_type: RoomType
    confidence: float
    openings: List[DetectedOpening]
    infrastructure: List[DetectedInfrastructure]
    dimensions: Dict  # largura, profundidade, altura
    colors: Dict  # cores das paredes
    materials: Dict  # materiais detectados
    suggestions: List[str]  # sugestões da IA

class RoomAnalyzer:
    """Analisa um ambiente completo usando IA"""
    
    # Assinaturas de cada cômodo
    ROOM_SIGNATURES = {
        RoomType.KITCHEN: ["fogao", "pia", "geladeira", "armario", "bancada", "coifa"],
        RoomType.BATHROOM: ["vaso", "pia", "chuveiro", "box", "espelho", "armario_banheiro"],
        RoomType.LIVING_ROOM: ["sofa", "rack", "tv", "mesa_centro", "poltrona", "tapete"],
        RoomType.BEDROOM: ["cama", "guarda_roupa", "criado_mudo", "abajur", "tv_quarto"],
        RoomType.LAUNDRY: ["maquina_lavar", "tanque", "varal", "cesto_roupa"],
        RoomType.OFFICE: ["mesa_escritorio", "cadeira_office", "monitor", "estante"],
    }
    
    # Objetos de referência para escala
    REFERENCE_SIZES = {
        "porta": {"width": 0.80, "height": 2.10},  # metros
        "janela_standard": {"width": 1.50, "height": 1.20},
        "tomada": {"height": 0.10},  # 10cm padrão brasileiro
        "azulejo": {"size": 0.30},   # 30cm
        "tijolo": {"length": 0.19},  # 19cm
    }
    
    def __init__(self):
        # Simulação de detecção (em produção, usaria YOLOv8 + SAM2)
        self.detected_objects = []
    
    def analyze_room(self, image: np.ndarray) -> RoomAnalysis:
        """
        Analisa um cômodo completo
        
        Args:
            image: Imagem do cômodo
        
        Returns:
            RoomAnalysis com todas as informações
        """
        h, w = image.shape[:2]
        
        # 1. Classificar tipo de cômodo
        room_type, room_conf = self._classify_room(image)
        
        # 2. Detectar aberturas (janelas, portas)
        openings = self._detect_openings(image)
        
        # 3. Detectar infraestrutura (tomadas, pontos de água)
        infrastructure = self._detect_infrastructure(image)
        
        # 4. Estimar dimensões
        dimensions = self._estimate_dimensions(image)
        
        # 5. Analisar cores das paredes
        colors = self._analyze_colors(image)
        
        # 6. Detectar materiais existentes
        materials = self._detect_materials(image)
        
        # 7. Gerar sugestões
        suggestions = self._generate_suggestions(room_type, openings, dimensions)
        
        return RoomAnalysis(
            room_type=room_type,
            confidence=room_conf,
            openings=openings,
            infrastructure=infrastructure,
            dimensions=dimensions,
            colors=colors,
            materials=materials,
            suggestions=suggestions
        )
    
    def _classify_room(self, image: np.ndarray) -> Tuple[RoomType, float]:
        """Classifica o tipo de cômodo"""
        # Simulação - em produção usaria YOLOv8 + classificador
        h, w = image.shape[:2]
        aspect_ratio = w / h
        
        # Heurísticas básicas (depois substituir por IA real)
        if aspect_ratio > 1.5:
            return RoomType.LIVING_ROOM, 0.75
        elif aspect_ratio < 0.8:
            return RoomType.HALLWAY, 0.60
        else:
            return RoomType.BEDROOM, 0.65
    
    def _detect_openings(self, image: np.ndarray) -> List[DetectedOpening]:
        """Detecta janelas e portas usando processamento de imagem"""
        openings = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Encontrar contornos retangulares
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:  # Filtrar ruído
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            # Classificar como porta ou janela
            if 0.3 < aspect_ratio < 0.8 and area > 5000:
                openings.append(DetectedOpening(
                    type=OpeningType.DOOR,
                    x=x, y=y, width=w, height=h,
                    confidence=0.75,
                    dimensions_cm={"width": w/10, "height": h/10}
                ))
            elif 0.5 < aspect_ratio < 2.5 and area > 3000:
                openings.append(DetectedOpening(
                    type=OpeningType.WINDOW,
                    x=x, y=y, width=w, height=h,
                    confidence=0.70,
                    dimensions_cm={"width": w/10, "height": h/10}
                ))
        
        return openings
    
    def _detect_infrastructure(self, image: np.ndarray) -> List[DetectedInfrastructure]:
        """Detecta tomadas, interruptores, pontos de água"""
        infra = []
        h, w = image.shape[:2]
        
        # Simulação de detecção
        # Em produção: YOLOv8 treinado para tomadas/interruptores brasileiros
        
        # Heurística: tomadas ficam a ~30cm do chão
        bottom_region = image[int(h*0.7):h, :]
        
        # Detectar pequenos retângulos brancos (tomadas)
        gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 2000:  # Tamanho típico de tomada
                x, y, w, h_box = cv2.boundingRect(contour)
                aspect = w / h_box if h_box > 0 else 0
                
                if 0.5 < aspect < 2.0:  # Quase quadrado
                    infra.append(DetectedInfrastructure(
                        type=InfrastructureType.OUTLET,
                        x=x, y=y + int(h*0.7),
                        confidence=0.60,
                        subtype="2P+T"
                    ))
        
        return infra
    
    def _estimate_dimensions(self, image: np.ndarray) -> Dict:
        """Estima dimensões do cômodo"""
        h, w = image.shape[:2]
        
        # Usar referências para escala
        return {
            "width_meters": round(w / 500, 1),   # Estimativa grosseira
            "depth_meters": round(h / 400, 1),
            "height_meters": 2.6,  # Padrão brasileiro
            "area_m2": round((w/500) * (h/400), 1),
            "confidence": 0.5  # Baixa confiança sem referência
        }
    
    def _analyze_colors(self, image: np.ndarray) -> Dict:
        """Analisa as cores das paredes"""
        h, w = image.shape[:2]
        
        # Pegar regiões das paredes (laterais e topo)
        wall_regions = [
            image[0:h, 0:50],     # Parede esquerda
            image[0:h, w-50:w],   # Parede direita
            image[0:50, 0:w],     # Teto
        ]
        
        colors = []
        for region in wall_regions:
            avg_color = np.mean(region, axis=(0, 1))
            colors.append({
                "rgb": [int(c) for c in avg_color],
                "hex": f"#{int(avg_color[2]):02x}{int(avg_color[1]):02x}{int(avg_color[0]):02x}",
                "name": self._color_name(avg_color)
            })
        
        return {"walls": colors, "count": len(colors)}
    
    def _color_name(self, rgb: np.ndarray) -> str:
        """Converte RGB para nome de cor"""
        r, g, b = rgb
        if r > 200 and g > 200 and b > 200: return "Branco"
        if r < 50 and g < 50 and b < 50: return "Preto"
        if r > g and r > b: return "Tons de vermelho"
        if g > r and g > b: return "Tons de verde"
        if b > r and b > g: return "Tons de azul"
        if abs(r - g) < 30 and abs(g - b) < 30: return "Cinza"
        return "Bege/Creme"
    
    def _detect_materials(self, image: np.ndarray) -> Dict:
        """Detecta materiais existentes"""
        # Simulação - em produção usaria classificador de texturas
        return {
            "floor": {"type": "ceramica", "confidence": 0.6},
            "walls": {"type": "pintura", "confidence": 0.8},
            "ceiling": {"type": "gesso", "confidence": 0.5}
        }
    
    def _generate_suggestions(self, room_type: RoomType, 
                             openings: List[DetectedOpening],
                             dimensions: Dict) -> List[str]:
        """Gera sugestões baseadas no cômodo"""
        suggestions = []
        area = dimensions.get("area_m2", 0)
        
        if room_type == RoomType.LIVING_ROOM:
            if area > 25:
                suggestions.append("Ambiente amplo - ideal para sofá de canto")
                suggestions.append("Considere um painel de TV até 75 polegadas")
                suggestions.append("Dá para dividir em dois ambientes: estar + jantar")
            else:
                suggestions.append("Sofá retrátil economiza espaço")
                suggestions.append("TV de até 55 polegadas é ideal")
        
        elif room_type == RoomType.BATHROOM:
            if area > 4:
                suggestions.append("Espaço suficiente para banheira de hidromassagem")
                suggestions.append("Dá para ter box e banheira separados")
            else:
                suggestions.append("Box de canto otimiza espaço")
                suggestions.append("Banheira não recomendada - espaço insuficiente")
        
        elif room_type == RoomType.BEDROOM:
            if area > 15:
                suggestions.append("Cabe cama king size + closet")
                suggestions.append("Dá para ter uma poltrona de leitura")
            else:
                suggestions.append("Cama queen size é o ideal")
                suggestions.append("Guarda-roupa com portas de correr")
        
        return suggestions