from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# ============ Modelos ============

@dataclass
class Material:
    name: str
    quantity: float
    unit: str
    category: str
    unit_price: Optional[float] = None
    total_price: Optional[float] = None

@dataclass
class Product:
    name: str
    brand: str
    price: float
    store: str
    url: str
    available: bool
    delivery_time: str

class MaterialCalculator:
    """Calcula materiais necessários baseado nas medidas"""
    
    PAINT_COVERAGE = 10
    GROUT_COVERAGE = 4
    FLOOR_WASTE = 0.10
    WALL_WASTE = 0.05
    
    def __init__(self, measurements: Dict):
        self.measurements = measurements
        self.materials: List[Material] = []
    
    def calculate_floor(self) -> List[Material]:
        area = self.measurements.get("floor_area_m2", 0)
        perimeter = self.measurements.get("floor_perimeter_m", 0)
        materials = []
        
        if area > 0:
            floor_qty = area * (1 + self.FLOOR_WASTE)
            materials.append(Material("Piso/Revestimento", round(floor_qty, 2), "m²", "piso"))
            materials.append(Material("Argamassa para piso", round(area * 5, 2), "kg", "piso"))
            materials.append(Material("Rejunte", round(area / self.GROUT_COVERAGE, 2), "kg", "piso"))
        
        if perimeter > 0:
            materials.append(Material("Rodapé", round(perimeter, 2), "m", "acabamento"))
        
        self.materials.extend(materials)
        return materials
    
    def calculate_walls(self) -> List[Material]:
        wall_area = self.measurements.get("wall_area_m2", 0)
        wall_height = self.measurements.get("wall_height_m", 2.6)
        wall_perimeter = self.measurements.get("wall_perimeter_m", 0)
        materials = []
        
        if wall_area > 0:
            paint_qty = wall_area / (self.PAINT_COVERAGE / 2)
            materials.append(Material("Tinta látex", round(paint_qty, 1), "litros", "pintura"))
            materials.append(Material("Massa corrida", round(wall_area * 0.5, 1), "kg", "pintura"))
            materials.append(Material("Selador", round(wall_area / 8, 1), "litros", "pintura"))
        
        if wall_perimeter > 0 and wall_height > 0:
            gesso_area = wall_perimeter * wall_height
            materials.append(Material("Gesso acartonado", round(gesso_area, 2), "m²", "parede"))
        
        self.materials.extend(materials)
        return materials
    
    def calculate_openings(self) -> List[Material]:
        openings = self.measurements.get("openings", [])
        materials = []
        
        for opening in openings:
            if opening.get("type") == "door":
                w = opening.get("width", 0.8)
                h = opening.get("height", 2.1)
                materials.append(Material(f"Porta ({w}x{h}m)", 1, "unidade", "porta"))
                materials.append(Material("Kit porta (dobradiças, fechadura)", 1, "kit", "porta"))
            elif opening.get("type") == "window":
                w = opening.get("width", 1.2)
                h = opening.get("height", 1.0)
                materials.append(Material(f"Janela ({w}x{h}m)", 1, "unidade", "janela"))
        
        self.materials.extend(materials)
        return materials
    
    def calculate_electrical(self) -> List[Material]:
        perimeter = self.measurements.get("wall_perimeter_m", 0)
        area = self.measurements.get("floor_area_m2", 0)
        
        outlets = max(2, int(perimeter / 3))
        lights = max(1, int(area / 6))
        
        materials = [
            Material("Tomadas 2P+T", outlets, "unidade", "elétrica"),
            Material("Espelhos para tomada", outlets, "unidade", "elétrica"),
            Material("Pontos de luz", lights, "unidade", "elétrica"),
            Material("Fio 2.5mm²", round(perimeter * 2, 1), "metros", "elétrica"),
            Material("Disjuntor 20A", 2, "unidade", "elétrica"),
        ]
        
        self.materials.extend(materials)
        return materials
    
    def calculate_all(self) -> Dict:
        self.materials = []
        self.calculate_floor()
        self.calculate_walls()
        self.calculate_openings()
        self.calculate_electrical()
        
        categories = {}
        for m in self.materials:
            if m.category not in categories:
                categories[m.category] = []
            categories[m.category].append({"name": m.name, "quantity": m.quantity, "unit": m.unit})
        
        return {
            "materials": [{"name": m.name, "quantity": m.quantity, "unit": m.unit, "category": m.category} for m in self.materials],
            "categories": categories,
            "summary": {
                "total_items": len(self.materials),
                "categories_count": len(categories)
            }
        }


class ProductFinder:
    """Busca produtos nas lojas"""
    
    CATALOG = {
        "piso": [
            {"name": "Piso Laminado Carvalho", "brand": "Duratex", "price": 29.90, "store": "Leroy Merlin", "url": "", "available": True, "delivery_time": "3 dias"},
            {"name": "Piso Vinílico Premium", "brand": "Tarkett", "price": 45.00, "store": "Telhanorte", "url": "", "available": True, "delivery_time": "5 dias"},
            {"name": "Porcelanato Polido", "brand": "Eliane", "price": 59.90, "store": "C&C", "url": "", "available": True, "delivery_time": "2 dias"},
        ],
        "pintura": [
            {"name": "Tinta Suvinil Toque de Seda", "brand": "Suvinil", "price": 189.90, "store": "Leroy Merlin", "url": "", "available": True, "delivery_time": "1 dia"},
            {"name": "Tinta Coral Decora", "brand": "Coral", "price": 159.90, "store": "Telhanorte", "url": "", "available": True, "delivery_time": "2 dias"},
        ],
        "acabamento": [
            {"name": "Rodapé Branco 2m", "brand": "Santa Luzia", "price": 18.00, "store": "Leroy Merlin", "url": "", "available": True, "delivery_time": "1 dia"},
            {"name": "Rodapé Madeira 2.4m", "brand": "Eucatex", "price": 25.00, "store": "C&C", "url": "", "available": True, "delivery_time": "3 dias"},
        ],
        "parede": [
            {"name": "Placa Gesso 60x60cm", "brand": "Knauf", "price": 12.00, "store": "Leroy Merlin", "url": "", "available": True, "delivery_time": "2 dias"},
            {"name": "Gesso Acartonado 1.2x2.4m", "brand": "Placo", "price": 35.00, "store": "Telhanorte", "url": "", "available": True, "delivery_time": "1 dia"},
        ],
        "porta": [
            {"name": "Porta Pronta 80x210cm", "brand": "Pormade", "price": 299.00, "store": "Leroy Merlin", "url": "", "available": True, "delivery_time": "5 dias"},
        ],
        "janela": [
            {"name": "Janela Alumínio 150x120cm", "brand": "Alcoa", "price": 450.00, "store": "C&C", "url": "", "available": True, "delivery_time": "7 dias"},
        ],
        "elétrica": [
            {"name": "Tomada 2P+T", "brand": "Tramontina", "price": 8.90, "store": "Leroy Merlin", "url": "", "available": True, "delivery_time": "1 dia"},
            {"name": "Fio 2.5mm²", "brand": "Sil", "price": 3.50, "store": "Telhanorte", "url": "", "available": True, "delivery_time": "1 dia"},
        ],
    }
    
    def search(self, category: str) -> List[Dict]:
        return self.CATALOG.get(category, [])
    
    def calculate_total(self, materials: List[Dict]) -> Dict:
        total_by_store = {}
        items = []
        
        for material in materials:
            products = self.search(material.get("category", ""))
            if products:
                best = min(products, key=lambda p: p["price"])
                quantity = material["quantity"]
                unit_price = best["price"]
                
                # Ajustar quantidade para itens unitários
                if material["unit"] == "unidade":
                    total_item = quantity * unit_price
                elif material["unit"] == "kit":
                    total_item = quantity * unit_price
                elif material["unit"] == "metros":
                    total_item = quantity * unit_price
                else:
                    total_item = quantity * unit_price
                
                items.append({
                    "material": material["name"],
                    "quantity": quantity,
                    "unit": material["unit"],
                    "product": best["name"],
                    "brand": best["brand"],
                    "store": best["store"],
                    "unit_price": unit_price,
                    "total": round(total_item, 2),
                    "delivery": best["delivery_time"]
                })
                
                store = best["store"]
                if store not in total_by_store:
                    total_by_store[store] = 0
                total_by_store[store] += total_item
        
        best_store = min(total_by_store, key=total_by_store.get) if total_by_store else None
        
        return {
            "items": items,
            "totals_by_store": {k: round(v, 2) for k, v in total_by_store.items()},
            "best_store": best_store,
            "best_total": round(total_by_store.get(best_store, 0), 2) if best_store else 0,
            "total_items": len(items)
        }


# ============ Endpoints ============

@router.post("/calculate-materials/{project_id}")
async def calculate_materials(project_id: str):
    """Calcula materiais necessários e busca preços"""
    
    # Buscar medidas do projeto
    floor_data_path = f"outputs/{project_id}/floorplan/floor_plan.json"
    
    if os.path.exists(floor_data_path):
        with open(floor_data_path, "r") as f:
            floor_data = json.load(f)
        dims = floor_data.get("dimensions", {})
        measurements = {
            "floor_area_m2": dims.get("area_sqm", 42),
            "floor_perimeter_m": dims.get("width_meters", 5) * 2 + dims.get("depth_meters", 4) * 2,
            "wall_area_m2": (dims.get("width_meters", 5) * 2 + dims.get("depth_meters", 4) * 2) * 2.6,
            "wall_height_m": 2.6,
            "wall_perimeter_m": dims.get("width_meters", 5) * 2 + dims.get("depth_meters", 4) * 2,
            "openings": floor_data.get("openings", [])
        }
    else:
        # Medidas de exemplo
        measurements = {
            "floor_area_m2": 42,
            "floor_perimeter_m": 26,
            "wall_area_m2": 90,
            "wall_height_m": 2.6,
            "wall_perimeter_m": 26,
            "openings": [
                {"type": "door", "width": 0.8, "height": 2.1},
                {"type": "window", "width": 1.5, "height": 1.2}
            ]
        }
    
    # Calcular materiais
    calc = MaterialCalculator(measurements)
    materials_result = calc.calculate_all()
    
    # Buscar preços
    finder = ProductFinder()
    prices = finder.calculate_total(materials_result["materials"])
    
    return {
        "project_id": project_id,
        "measurements": measurements,
        "materials": materials_result["materials"],
        "categories": materials_result["categories"],
        "prices": prices,
        "summary": {
            "total_materials": len(materials_result["materials"]),
            "best_store": prices["best_store"],
            "best_total": prices["best_total"],
            "stores_compared": list(prices["totals_by_store"].keys()),
            "message": f"💰 Economize comprando na {prices['best_store']}: R$ {prices['best_total']:.2f}"
        }
    }

@router.get("/products/{category}")
async def get_products(category: str):
    """Lista produtos de uma categoria"""
    finder = ProductFinder()
    products = finder.search(category)
    return {
        "category": category,
        "products": products,
        "count": len(products)
    }

@router.get("/categories")
async def list_categories():
    """Lista categorias disponíveis"""
    finder = ProductFinder()
    categories = list(finder.CATALOG.keys())
    return {
        "categories": categories,
        "count": len(categories)
    }

@router.post("/budget/{project_id}")
async def generate_budget(
    project_id: str,
    store: str = Form(None)
):
    """Gera orçamento completo para uma loja específica"""
    
    # Calcular materiais
    floor_data_path = f"outputs/{project_id}/floorplan/floor_plan.json"
    
    if os.path.exists(floor_data_path):
        with open(floor_data_path, "r") as f:
            floor_data = json.load(f)
        dims = floor_data.get("dimensions", {})
        measurements = {
            "floor_area_m2": dims.get("area_sqm", 42),
            "floor_perimeter_m": dims.get("width_meters", 5) * 2 + dims.get("depth_meters", 4) * 2,
            "wall_height_m": 2.6,
            "wall_perimeter_m": dims.get("width_meters", 5) * 2 + dims.get("depth_meters", 4) * 2,
            "openings": floor_data.get("openings", [])
        }
    else:
        measurements = {
            "floor_area_m2": 42,
            "floor_perimeter_m": 26,
            "wall_height_m": 2.6,
            "wall_perimeter_m": 26,
            "openings": []
        }
    
    # Calcular materiais
    calc = MaterialCalculator(measurements)
    materials_result = calc.calculate_all()
    
    # Buscar preços
    finder = ProductFinder()
    all_prices = finder.calculate_total(materials_result["materials"])
    
    # Filtrar por loja se especificada
    if store:
        items = [item for item in all_prices["items"] if item["store"] == store]
        total = sum(item["total"] for item in items)
    else:
        items = all_prices["items"]
        store = all_prices["best_store"]
        total = all_prices["best_total"]
    
    return {
        "project_id": project_id,
        "store": store,
        "items": items,
        "total": round(total, 2),
        "delivery_estimate": "5 a 10 dias úteis",
        "payment_methods": ["Cartão de crédito", "Boleto", "PIX"],
        "installments": "Até 10x sem juros"
    }