"""
Calculadora Automática de Materiais
Converte medidas em quantidades de produtos
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Material:
    name: str
    quantity: float
    unit: str
    category: str
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    suppliers: List[str] = None

class MaterialCalculator:
    """Calcula materiais necessários baseado nas medidas"""
    
    # Rendimentos padrão
    PAINT_COVERAGE = 10  # m² por litro (2 demãos)
    GROUT_COVERAGE = 4   # m² por kg (rejunte)
    FLOOR_WASTE = 0.10   # 10% de perda para pisos
    WALL_WASTE = 0.05    # 5% de perda para paredes
    
    def __init__(self, measurements: Dict):
        self.measurements = measurements
        self.materials: List[Material] = []
    
    def calculate_floor(self) -> List[Material]:
        """Calcula materiais para piso"""
        area = self.measurements.get("floor_area_m2", 0)
        perimeter = self.measurements.get("floor_perimeter_m", 0)
        
        materials = []
        
        if area > 0:
            # Piso (com 10% de perda)
            floor_qty = area * (1 + self.FLOOR_WASTE)
            materials.append(Material(
                name="Piso/Revestimento",
                quantity=round(floor_qty, 2),
                unit="m²",
                category="piso"
            ))
            
            # Argamassa (aproximadamente 5 kg/m²)
            materials.append(Material(
                name="Argamassa para piso",
                quantity=round(area * 5, 2),
                unit="kg",
                category="piso"
            ))
            
            # Rejunte
            materials.append(Material(
                name="Rejunte",
                quantity=round(area / self.GROUT_COVERAGE, 2),
                unit="kg",
                category="piso"
            ))
        
        if perimeter > 0:
            # Rodapé
            materials.append(Material(
                name="Rodapé",
                quantity=round(perimeter, 2),
                unit="m",
                category="acabamento"
            ))
        
        self.materials.extend(materials)
        return materials
    
    def calculate_walls(self) -> List[Material]:
        """Calcula materiais para paredes"""
        wall_area = self.measurements.get("wall_area_m2", 0)
        wall_height = self.measurements.get("wall_height_m", 2.6)
        wall_perimeter = self.measurements.get("wall_perimeter_m", 0)
        
        materials = []
        
        if wall_area > 0:
            # Tinta (1 demão = 5 m²/L, 2 demãos = cobertura/2)
            paint_qty = wall_area / (self.PAINT_COVERAGE / 2)
            materials.append(Material(
                name="Tinta látex",
                quantity=round(paint_qty, 1),
                unit="litros",
                category="pintura"
            ))
            
            # Massa corrida
            materials.append(Material(
                name="Massa corrida",
                quantity=round(wall_area * 0.5, 1),
                unit="kg",
                category="pintura"
            ))
            
            # Selador
            materials.append(Material(
                name="Selador",
                quantity=round(wall_area / 8, 1),
                unit="litros",
                category="pintura"
            ))
        
        if wall_perimeter > 0 and wall_height > 0:
            # Gesso (perímetro x altura)
            gesso_area = wall_perimeter * wall_height
            materials.append(Material(
                name="Gesso acartonado",
                quantity=round(gesso_area, 2),
                unit="m²",
                category="parede"
            ))
        
        self.materials.extend(materials)
        return materials
    
    def calculate_openings(self) -> List[Material]:
        """Calcula materiais para portas e janelas"""
        openings = self.measurements.get("openings", [])
        materials = []
        
        for opening in openings:
            if opening.get("type") == "door":
                materials.append(Material(
                    name=f"Porta ({opening.get('width', 0.8)}x{opening.get('height', 2.1)}m)",
                    quantity=1,
                    unit="unidade",
                    category="porta"
                ))
                materials.append(Material(
                    name="Kit porta (dobradiças, fechadura)",
                    quantity=1,
                    unit="kit",
                    category="porta"
                ))
            elif opening.get("type") == "window":
                materials.append(Material(
                    name=f"Janela ({opening.get('width', 1.2)}x{opening.get('height', 1.0)}m)",
                    quantity=1,
                    unit="unidade",
                    category="janela"
                ))
        
        self.materials.extend(materials)
        return materials
    
    def calculate_electrical(self) -> List[Material]:
        """Calcula materiais elétricos básicos"""
        perimeter = self.measurements.get("wall_perimeter_m", 0)
        area = self.measurements.get("floor_area_m2", 0)
        
        # Estimativa: 1 tomada a cada 3m, 1 ponto de luz a cada 6m²
        outlets = max(2, int(perimeter / 3))
        lights = max(1, int(area / 6))
        
        materials = [
            Material(name="Tomadas 2P+T", quantity=outlets, unit="unidade", category="elétrica"),
            Material(name="Espelhos para tomada", quantity=outlets, unit="unidade", category="elétrica"),
            Material(name="Pontos de luz", quantity=lights, unit="unidade", category="elétrica"),
            Material(name="Fio 2.5mm²", quantity=round(perimeter * 2, 1), unit="metros", category="elétrica"),
            Material(name="Disjuntor 20A", quantity=2, unit="unidade", category="elétrica"),
        ]
        
        self.materials.extend(materials)
        return materials
    
    def calculate_all(self) -> Dict:
        """Calcula todos os materiais"""
        self.materials = []
        
        self.calculate_floor()
        self.calculate_walls()
        self.calculate_openings()
        self.calculate_electrical()
        
        # Agrupar por categoria
        categories = {}
        for material in self.materials:
            cat = material.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "name": material.name,
                "quantity": material.quantity,
                "unit": material.unit
            })
        
        total_items = len(self.materials)
        total_quantity = sum(m.quantity for m in self.materials if m.unit != "unidade")
        
        return {
            "measurements": self.measurements,
            "materials": [{"name": m.name, "quantity": m.quantity, "unit": m.unit, "category": m.category} for m in self.materials],
            "categories": categories,
            "summary": {
                "total_items": total_items,
                "total_quantity": round(total_quantity, 2),
                "categories_count": len(categories)
            }
        }


# Exemplo de uso
if __name__ == "__main__":
    measurements = {
        "floor_area_m2": 42,
        "floor_perimeter_m": 26,
        "wall_area_m2": 90,
        "wall_height_m": 2.6,
        "wall_perimeter_m": 26,
        "openings": [
            {"type": "door", "width": 0.8, "height": 2.1},
            {"type": "window", "width": 1.5, "height": 1.2},
            {"type": "window", "width": 1.0, "height": 1.0}
        ]
    }
    
    calc = MaterialCalculator(measurements)
    result = calc.calculate_all()
    
    print("📊 Materiais necessários:")
    for material in result["materials"]:
        print(f"  • {material['name']}: {material['quantity']} {material['unit']}")