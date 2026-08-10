import os
import json
import time
import secrets
from urllib import response
import httpx
from dotenv import load_dotenv
from langchain_core.tools import tool
import qrcode
import base64
from io import BytesIO

from vector_store import search_products

load_dotenv()

DJANGO_API_URL = os.getenv("DJANGO_INTERNAL_API_URL")
DJANGO_API_KEY = os.getenv("DJANGO_INTERNAL_API_KEY")
HEADERS = {"X-Internal-Key": DJANGO_API_KEY}

TOKEN_TTL_SECONDS = 300
_pending_orders = {}


def _build_payment_qr(order_id: int) -> str:
    """Internal helper, NOT a tool — only ever called automatically by confirm_order."""
    payment_url = f"http://localhost:8000/orders/{order_id}/pay/"
    img = qrcode.make(payment_url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def build_tools_for_user(user_id: int):
    @tool
    def search_catalog(query: str) -> str:
        """Search the product catalog using natural language."""
        hits = search_products(query, n_results=5)
        return json.dumps(hits)

    @tool
    def get_product_details(product_id: int) -> str:
        """Get full details of a specific product by its ID."""
        response = httpx.get(f"{DJANGO_API_URL}/products/{product_id}/", headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return json.dumps({"error": "Product not found"})
        return response.text

    @tool
    def add_to_cart(product_id: int, quantity: int = 1) -> str:
        """Add a product to the current customer's cart."""
        response = httpx.post(
            f"{DJANGO_API_URL}/cart/add/",
            headers=HEADERS,
            json={"user_id": user_id, "product_id": product_id, "quantity": quantity},
            timeout=15,
        )
        return response.text

    
    @tool
    def preview_order(shipping_address: str, payment_method: str = "esewa") -> str:
        """Show what the customer's order would look like WITHOUT placing it.
        payment_method must be one of: esewa, khalti, card, cod (cash on delivery).
        Always call this first — never skip to confirm_order."""
        token = secrets.token_hex(6)
        _pending_orders[token] = {
            "user_id": user_id,
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "created_at": time.time(),
        }
        return json.dumps({
            "preview": True,
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "confirmation_token": token,
            "expires_in_seconds": TOKEN_TTL_SECONDS,
            "note": "NOT placed yet. Ask the customer to confirm before calling confirm_order.",
        })

    @tool
    def confirm_order(confirmation_token: str) -> str:
        """Actually place the order. Only call this after the customer explicitly
        confirms, using the exact token from preview_order. A payment QR code is
        generated automatically on success — mention the customer can scan it to pay."""
        pending = _pending_orders.get(confirmation_token)
        if not pending:
            return json.dumps({"error": "Invalid or expired token. Call preview_order again."})

        if time.time() - pending["created_at"] > TOKEN_TTL_SECONDS:
            del _pending_orders[confirmation_token]
            return json.dumps({"error": "This order preview expired. Call preview_order again."})

        if pending["user_id"] != user_id:
            return json.dumps({"error": "Token does not belong to this user."})

        response = httpx.post(
            f"{DJANGO_API_URL}/checkout/",
            headers=HEADERS,
            json={k: v for k, v in pending.items() if k != "created_at"},
            timeout=15,
        )
        del _pending_orders[confirmation_token]

        result = response.json()
        if result.get("success") and pending["payment_method"] != "cod":
            order_id = result["order_id"]
            result["payment_qr_base64"] = _build_payment_qr(order_id)
            result["payment_url"] = f"http://localhost:8000/orders/{order_id}/pay/"

        return json.dumps(result)

    @tool
    def check_order_status() -> str:
        """Look up the current customer's recent order history."""
        response = httpx.get(f"{DJANGO_API_URL}/orders/{user_id}/", headers=HEADERS, timeout=15)
        return response.text

    return [search_catalog, get_product_details, add_to_cart, preview_order, confirm_order, check_order_status]