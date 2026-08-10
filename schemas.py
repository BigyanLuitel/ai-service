from typing import Optional
from pydantic import BaseModel

class DescriptionRequest(BaseModel):
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    raw_notes: Optional[str] = None
    specs: Optional[dict] = None

class DescriptionResponse(BaseModel):
    description: str

class CategoryRequest(BaseModel):
    name: str
    raw_notes: Optional[str] = None

class CategoryResponse(BaseModel):
    category: str
    confidence_note: str

class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


class SearchResult(BaseModel):
    product_id: int
    name: str
    price: str
    category: str
    in_stock: bool


class SearchResponse(BaseModel):
    results: list[SearchResult]
    

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    user_id: int

class ChatResponse(BaseModel):
    reply: str
    payment_qr_base64: Optional[str] = None
    payment_url: Optional[str] = None