import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DJANGO_API_URL = os.getenv("DJANGO_INTERNAL_API_URL")
DJANGO_API_KEY = os.getenv("DJANGO_INTERNAL_API_KEY")

HEADERS = {"X-Internal-Key": DJANGO_API_KEY}


def fetch_all_products():
    response = httpx.get(f"{DJANGO_API_URL}/products/", headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.json()["products"]