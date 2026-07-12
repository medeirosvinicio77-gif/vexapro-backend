"""
Buscador de Produtos nas Lojas
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    brand: str
    price: float
    store: str
    url: str
    available: bool
    delivery_time: str
    quantity_available: int

class ProductFinder:
    """Busca produtos nas lojas parceiras"""
    
    # Catálogo simulado (em produção, conectaria com APIs reais)
    CATALOG = {
        "piso": [
            Product("Piso Laminado Carvalho", "Duratex", 29.90, "Leroy Merlin", "", True, "3 dias", 100),
            Product("Piso Vinílico Premium", "Tarkett", 45.00, "Telhanorte", "", True, "5 dias", 50),
            Product("Porcelanato Polido", "Eliane", 59.90, "C&C", "", True, "2 dias", 200),
        ],
        "tinta": [
            Product("Tinta Suvinil Toque de Seda", "Suvinil", 189.90, "Leroy Merlin", "", True, "1 dia", 50),
            Product("Tinta Coral Decora", "Coral", 159.90, "Telhanorte", "", True, "2 dias", 80),
        ],
        "rodapé": [
            Product("Rodapé Branco 2m", "Santa Luzia", 18.00, "Leroy Merlin", "", True, "1 dia", 200),
            Product("Rodapé Madeira 2.4m", "Eucatex", 25.00, "C&C", "", True, "3 dias", 150),
        ],
        "gesso": [
            Product("Placa Gesso 60x60cm", "Knauf", 12.00, "Leroy Merlin", "", True, "2 dias", 300),
            Product("Gesso Acartonado 1.2x2.4m", "Placo", 35.00, "Telhanorte", "", True, "1 dia", 100),
        ],
    }
    
    def search(self, category: str, max_results: int = 5) -> List[Product]:
        """Busca produtos por categoria"""
        return self.CATALOG.get(category, [])[:max_results]
    
    def get_best_price(self, category: str) -> Optional[Product]:
        """Retorna o produto com menor preço"""
        products = self.search(category)
        if products:
            return min(products, key=lambda p: p.price)
        return None
    
    def compare_stores(self, category: str) -> List[Dict]:
        """Compara preços entre lojas"""
        products = self.search(category)
        comparison = []
        
        for product in products:
            comparison.append({
                "store": product.store,
                "brand": product.brand,
                "price": product.price,
                "delivery": product.delivery_time
            })
        
        return sorted(comparison, key=lambda x: x["price"])
    
    def calculate_total(self, materials: List[Dict]) -> Dict:
        """Calcula o total para uma lista de materiais"""
        total_by_store = {}
        items = []
        
        for material in materials:
            products = self.search(material["category"])
            if products:
                best = min(products, key=lambda p: p.price)
                quantity = material["quantity"]
                unit_price = best.price
                total_item = quantity * unit_price
                
                items.append({
                    "material": material["name"],
                    "quantity": quantity,
                    "unit": material["unit"],
                    "product": best.name,
                    "store": best.store,
                    "unit_price": unit_price,
                    "total": round(total_item, 2)
                })
                
                # Acumular por loja
                store = best.store
                if store not in total_by_store:
                    total_by_store[store] = 0
                total_by_store[store] += total_item
        
        # Melhor loja
        best_store = min(total_by_store, key=total_by_store.get) if total_by_store else None
        
        return {
            "items": items,
            "totals_by_store": {k: round(v, 2) for k, v in total_by_store.items()},
            "best_store": best_store,
            "best_total": round(total_by_store.get(best_store, 0), 2) if best_store else 0,
            "total_items": len(items)
        }