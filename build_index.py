from django_client import fetch_all_products
from vector_store import index_products

products = fetch_all_products()
count = index_products(products)
print(f"Indexed {count} products.")