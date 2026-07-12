from fastapi import APIRouter, Form, Query
from vision.room_analyzer import RoomAnalyzer, RoomType
from marketplace.design_catalog import DesignCatalog, ProductCategory
import json

router = APIRouter(prefix="/design", tags=["design"])

@router.post("/analyze-room/{project_id}")
async def analyze_room(project_id: str):
    """Analisa o ambiente e retorna sugestões de design"""
    
    # Em produção: carregar imagem do projeto
    # Por enquanto, retorna análise simulada
    
    analyzer = RoomAnalyzer()
    
    # Mock de imagem (depois usar a real)
    import numpy as np
    mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8) + 200
    
    analysis = analyzer.analyze_room(mock_image)
    
    # Buscar produtos recomendados
    recommended_products = []
    
    if analysis.room_type == RoomType.LIVING_ROOM:
        recommended_products = DesignCatalog.get_by_category(ProductCategory.SOFA)[:2]
        recommended_products += DesignCatalog.get_by_category(ProductCategory.CHANDELIER)[:1]
        recommended_products += DesignCatalog.get_by_category(ProductCategory.CURTAIN)[:1]
        recommended_products += DesignCatalog.get_by_category(ProductCategory.FLOOR)[:2]
    
    elif analysis.room_type == RoomType.BATHROOM:
        recommended_products = DesignCatalog.get_by_category(ProductCategory.BATHTUB)
    
    elif analysis.room_type == RoomType.BEDROOM:
        recommended_products = DesignCatalog.get_by_category(ProductCategory.CABINET)[:2]
    
    return {
        "project_id": project_id,
        "room_type": analysis.room_type.value,
        "confidence": analysis.confidence,
        "dimensions": analysis.dimensions,
        "openings_detected": len(analysis.openings),
        "infrastructure_detected": len(analysis.infrastructure),
        "colors_detected": analysis.colors,
        "materials_detected": analysis.materials,
        "suggestions": analysis.suggestions,
        "recommended_products": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value,
                "price": p.price,
                "colors": p.colors,
                "image_url": p.image_url,
                "dimensions": p.dimensions
            }
            for p in recommended_products
        ],
        "available_categories": DesignCatalog.get_all_categories(),
        "mdf_colors": DesignCatalog.get_mdf_colors(),
        "wall_colors": DesignCatalog.get_wall_colors()
    }

@router.get("/catalog/{category}")
async def get_catalog(
    category: str,
    query: str = Query(None),
    max_price: float = Query(None),
    color: str = Query(None)
):
    """Retorna produtos do catálogo com filtros"""
    
    # Converter string para enum
    try:
        cat_enum = ProductCategory(category)
    except ValueError:
        return {"error": f"Categoria '{category}' não encontrada"}
    
    products = DesignCatalog.get_by_category(cat_enum)
    
    # Aplicar filtros
    if query:
        products = [p for p in products if query.lower() in p.name.lower()]
    if max_price:
        products = [p for p in products if p.price <= max_price]
    if color:
        products = [p for p in products if any(color.lower() in c.lower() for c in p.colors)]
    
    return {
        "category": category,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "price": p.price,
                "dimensions": p.dimensions,
                "colors": p.colors,
                "materials": p.materials,
                "image_url": p.image_url,
                "rating": p.rating,
                "delivery_days": p.delivery_days
            }
            for p in products
        ],
        "count": len(products),
        "price_range": DesignCatalog.get_price_range(cat_enum)
    }

@router.get("/visualize/{product_id}")
async def visualize_product(product_id: str, color: str = Query(None)):
    """Retorna dados para visualização 3D do produto"""
    
    product = DesignCatalog.PRODUCTS.get(product_id)
    
    if not product:
        return {"error": "Produto não encontrado"}
    
    # Em produção: retornar modelo 3D real (GLB/glTF)
    return {
        "product_id": product.id,
        "name": product.name,
        "dimensions": product.dimensions,
        "available_colors": product.colors,
        "selected_color": color or product.colors[0],
        "materials": product.materials,
        "model_3d_available": product.model_3d_url is not None,
        "placement_guide": {
            "min_distance_from_wall": 0.10,
            "min_distance_from_door": 0.80,
            "recommended_height": product.dimensions["height"]
        }
    }

@router.get("/mdf-colors")
async def get_mdf_colors():
    """Retorna todas as cores de MDF disponíveis"""
    return {"colors": DesignCatalog.get_mdf_colors()}

@router.get("/wall-colors")
async def get_wall_colors():
    """Retorna cores de tinta para parede"""
    return {"colors": DesignCatalog.get_wall_colors()}

@router.post("/simulate/{project_id}")
async def simulate_environment(
    project_id: str,
    wall_color: str = Form(None),
    floor_type: str = Form(None),
    products: str = Form(None)  # JSON array de product_ids
):
    """
    Simula como o ambiente ficaria com as mudanças
    Retorna uma visualização gerada por IA
    """
    
    selected_products = json.loads(products) if products else []
    
    # Em produção: usar Stable Diffusion + ControlNet para gerar a imagem
    # Por enquanto, retorna uma simulação descritiva
    
    changes = []
    total_cost = 0
    
    if wall_color:
        changes.append(f"Parede pintada na cor {wall_color}")
    
    if floor_type:
        floor = DesignCatalog.PRODUCTS.get(floor_type)
        if floor:
            changes.append(f"Piso {floor.name} instalado")
            total_cost += floor.price * 42  # 42m² de exemplo
    
    for pid in selected_products:
        product = DesignCatalog.PRODUCTS.get(pid)
        if product:
            changes.append(f"{product.name} adicionado(a)")
            total_cost += product.price
    
    return {
        "project_id": project_id,
        "changes": changes,
        "total_estimated_cost": total_cost,
        "rendering_available": False,  # Em produção: True
        "message": "Simulação concluída! Visualize as mudanças no ambiente.",
        "next_steps": [
            "Visualize em 3D no Viewer",
            "Ajuste as cores e materiais",
            "Finalize o pedido no Marketplace"
        ]
    }