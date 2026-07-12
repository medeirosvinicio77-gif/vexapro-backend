"""
Catálogo de Produtos para Design de Interiores
Sofás, lustres, mesas, cortinas, pisos, banheiras, etc.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ProductCategory(Enum):
    SOFA = "sofa"
    ARMCHAIR = "poltrona"
    DINING_TABLE = "mesa_jantar"
    CHAIR = "cadeira"
    CHANDELIER = "lustre"
    LAMP = "abajur"
    CURTAIN = "cortina"
    RUG = "tapete"
    FLOOR = "piso"
    WALL_PAINT = "tinta_parede"
    BATHTUB = "banheira"
    AIR_CONDITIONER = "ar_condicionado"
    CABINET = "armario"
    TV_PANEL = "painel_tv"
    CUSTOM_FURNITURE = "movel_sob_medida"

@dataclass
class CatalogProduct:
    id: str
    name: str
    category: ProductCategory
    brand: str
    price: float
    dimensions: Dict  # {width, height, depth} em metros
    colors: List[str]
    materials: List[str]
    image_url: str
    model_3d_url: Optional[str] = None
    rating: float = 4.5
    in_stock: bool = True
    delivery_days: int = 7

class DesignCatalog:
    """Catálogo completo de produtos para design"""
    
    PRODUCTS = {
        # ===== SALA DE ESTAR =====
        "sofa_retratil_cinza": CatalogProduct(
            id="sofa_retratil_cinza",
            name="Sofá Retrátil Reclinável Milano",
            category=ProductCategory.SOFA,
            brand="Bartira",
            price=2899.00,
            dimensions={"width": 2.40, "height": 0.95, "depth": 1.05},
            colors=["Cinza Chumbo", "Bege Suede", "Azul Petróleo", "Verde Musgo"],
            materials=["Suede", "Espuma D33", "Estrutura Eucalipto"],
            image_url="https://exemplo.com/sofa_milano.jpg",
            rating=4.7
        ),
        "sofa_canto_reversivel": CatalogProduct(
            id="sofa_canto_reversivel",
            name="Sofá de Canto Reversível Toscana",
            category=ProductCategory.SOFA,
            brand="Via Design",
            price=4599.00,
            dimensions={"width": 3.20, "height": 0.90, "depth": 2.10},
            colors=["Linho Natural", "Cinza Grafite", "Mostarda"],
            materials=["Linho", "Espuma D45", "Estrutura Pinus"],
            image_url="https://exemplo.com/sofa_toscana.jpg",
            rating=4.9
        ),
        
        # ===== ILUMINAÇÃO =====
        "lustre_cristal": CatalogProduct(
            id="lustre_cristal",
            name="Lustre Cristal Veneza 12 Luzes",
            category=ProductCategory.CHANDELIER,
            brand="Yamamura",
            price=1890.00,
            dimensions={"width": 0.80, "height": 0.90, "depth": 0.80},
            colors=["Cristal Transparente", "Cristal Champagne"],
            materials=["Cristal", "Metal Cromado"],
            image_url="https://exemplo.com/lustre_veneza.jpg",
            rating=4.8
        ),
        "lustre_pendente_industrial": CatalogProduct(
            id="lustre_pendente_industrial",
            name="Pendente Industrial Vintage 3 Luzes",
            category=ProductCategory.CHANDELIER,
            brand="Allegra",
            price=459.00,
            dimensions={"width": 0.60, "height": 1.20, "depth": 0.30},
            colors=["Preto Fosco", "Cobre Escovado"],
            materials=["Metal", "Vidro Âmbar"],
            image_url="https://exemplo.com/pendente_industrial.jpg",
            rating=4.5
        ),
        
        # ===== MESA DE JANTAR =====
        "mesa_jantar_6_lugares": CatalogProduct(
            id="mesa_jantar_6_lugares",
            name="Mesa de Jantar Vidro Temperado 6 Lugares",
            category=ProductCategory.DINING_TABLE,
            brand="Província Móveis",
            price=2199.00,
            dimensions={"width": 1.80, "height": 0.76, "depth": 0.90},
            colors=["Vidro Transparente + Base Preta", "Vidro Transparente + Base Branca"],
            materials=["Vidro Temperado 12mm", "Metal"],
            image_url="https://exemplo.com/mesa_vidro.jpg",
            rating=4.6
        ),
        
        # ===== CORTINAS =====
        "cortina_blackout": CatalogProduct(
            id="cortina_blackout",
            name="Cortina Blackout Trilho Suave",
            category=ProductCategory.CURTAIN,
            brand="Lince",
            price=89.90,
            dimensions={"width": 2.50, "height": 2.60, "depth": 0.05},
            colors=["Branco", "Bege", "Cinza", "Azul Marinho", "Verde Bandeira"],
            materials=["Poliéster", "Blackout"],
            image_url="https://exemplo.com/cortina_blackout.jpg",
            rating=4.4
        ),
        
        # ===== PISOS =====
        "piso_vinilico_carvalho": CatalogProduct(
            id="piso_vinilico_carvalho",
            name="Piso Vinílico Carvalho Premium",
            category=ProductCategory.FLOOR,
            brand="Tarkett",
            price=59.90,
            dimensions={"width": 0.20, "height": 0.003, "depth": 1.22},
            colors=["Carvalho Claro", "Carvalho Médio", "Carvalho Escuro", "Café"],
            materials=["PVC", "Feltro"],
            image_url="https://exemplo.com/piso_vinilico.jpg",
            rating=4.7
        ),
        "piso_ceramico_portobello": CatalogProduct(
            id="piso_ceramico_portobello",
            name="Porcelanato Polido Portobello 60x60",
            category=ProductCategory.FLOOR,
            brand="Portobello",
            price=89.90,
            dimensions={"width": 0.60, "height": 0.008, "depth": 0.60},
            colors=["Branco Polido", "Bege Acetinado", "Cinza Natural", "Preto Absoluto"],
            materials=["Porcelanato"],
            image_url="https://exemplo.com/piso_portobello.jpg",
            rating=4.8
        ),
        
        # ===== BANHEIRO =====
        "banheira_hidro_160": CatalogProduct(
            id="banheira_hidro_160",
            name="Banheira de Hidromassagem Spa 160cm",
            category=ProductCategory.BATHTUB,
            brand="Jadot",
            price=4999.00,
            dimensions={"width": 1.60, "height": 0.55, "depth": 0.75},
            colors=["Branco Gelado", "Off-White"],
            materials=["Fibra de Vidro", "Acrílico"],
            image_url="https://exemplo.com/banheira_spa.jpg",
            rating=4.9
        ),
        
        # ===== AR CONDICIONADO =====
        "ar_condicionado_split_12000": CatalogProduct(
            id="ar_condicionado_split_12000",
            name="Ar Condicionado Split Inverter 12000 BTUs",
            category=ProductCategory.AIR_CONDITIONER,
            brand="Samsung",
            price=2899.00,
            dimensions={"width": 0.88, "height": 0.28, "depth": 0.22},
            colors=["Branco Premium"],
            materials=["Plástico ABS"],
            image_url="https://exemplo.com/ar_condicionado.jpg",
            rating=4.8
        ),
        
        # ===== MÓVEIS SOB MEDIDA =====
        "painel_tv_mdf": CatalogProduct(
            id="painel_tv_mdf",
            name="Painel para TV em MDF Sob Medida",
            category=ProductCategory.TV_PANEL,
            brand="VexaPro Móveis",
            price=1899.00,
            dimensions={"width": 3.00, "height": 2.40, "depth": 0.30},
            colors=["Branco TX", "Preto TX", "Carvalho", "Nogueira", "Avelã", "Freijó", "Amêndola"],
            materials=["MDF 18mm", "MDF 6mm (fundo)"],
            image_url="https://exemplo.com/painel_tv.jpg",
            rating=4.9
        ),
    }
    
    @classmethod
    def get_by_category(cls, category: ProductCategory) -> List[CatalogProduct]:
        """Retorna produtos de uma categoria"""
        return [p for p in cls.PRODUCTS.values() if p.category == category]
    
    @classmethod
    def get_all_categories(cls) -> List[Dict]:
        """Retorna todas as categorias disponíveis"""
        categories = set()
        for p in cls.PRODUCTS.values():
            categories.add({
                "id": p.category.value,
                "name": p.category.value.replace("_", " ").title()
            })
        return list(categories)
    
    @classmethod
    def search(cls, query: str, category: Optional[ProductCategory] = None) -> List[CatalogProduct]:
        """Busca produtos por nome ou categoria"""
        results = []
        query_lower = query.lower()
        
        for product in cls.PRODUCTS.values():
            if category and product.category != category:
                continue
            if query_lower in product.name.lower() or query_lower in product.brand.lower():
                results.append(product)
        
        return results
    
    @classmethod
    def get_price_range(cls, category: ProductCategory) -> Dict:
        """Retorna faixa de preços de uma categoria"""
        products = cls.get_by_category(category)
        if not products:
            return {"min": 0, "max": 0, "avg": 0}
        
        prices = [p.price for p in products]
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices)
        }
    
    @classmethod
    def get_mdf_colors(cls) -> List[Dict]:
        """Retorna todas as cores de MDF disponíveis"""
        return [
            {"name": "Branco TX", "hex": "#F5F5F5", "texture": "liso"},
            {"name": "Preto TX", "hex": "#1A1A1A", "texture": "liso"},
            {"name": "Carvalho", "hex": "#C4A882", "texture": "madeira"},
            {"name": "Nogueira", "hex": "#5C4033", "texture": "madeira"},
            {"name": "Avelã", "hex": "#B8956E", "texture": "madeira"},
            {"name": "Freijó", "hex": "#E8D5B7", "texture": "madeira"},
            {"name": "Amêndola", "hex": "#A0845C", "texture": "madeira"},
            {"name": "Wengue", "hex": "#3D2B1F", "texture": "madeira"},
            {"name": "Champagne", "hex": "#D4C5B2", "texture": "liso"},
            {"name": "Grafite", "hex": "#4A4A4A", "texture": "liso"},
        ]
    
    @classmethod
    def get_wall_colors(cls) -> List[Dict]:
        """Cores de tinta para parede"""
        return [
            {"name": "Branco Neve", "hex": "#FAFAFA", "brand": "Suvinil"},
            {"name": "Palha", "hex": "#E8D5B7", "brand": "Suvinil"},
            {"name": "Areia", "hex": "#D2B48C", "brand": "Coral"},
            {"name": "Terracota", "hex": "#CC7766", "brand": "Suvinil"},
            {"name": "Verde Água", "hex": "#9FE2BF", "brand": "Coral"},
            {"name": "Azul Serenidade", "hex": "#89CFF0", "brand": "Suvinil"},
            {"name": "Cinza Paris", "hex": "#B0B0B0", "brand": "Coral"},
            {"name": "Preto Fosco", "hex": "#2C2C2C", "brand": "Suvinil"},
        ]