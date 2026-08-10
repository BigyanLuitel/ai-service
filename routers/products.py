from fastapi import APIRouter, HTTPException

from schemas import CategoryResponse, DescriptionRequest, DescriptionResponse, CategoryRequest
from llm_client import generate_text

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/generate-description", response_model=DescriptionResponse)
def generate_description(payload: DescriptionRequest):
    specs_text = ""
    if payload.specs:
        specs_text = ", ".join(f"{k}: {v}" for k, v in payload.specs.items())

    context_lines = [f"Product name: {payload.name}"]
    if payload.brand:
        context_lines.append(f"Brand: {payload.brand}")
    if payload.category:
        context_lines.append(f"Category: {payload.category}")
    if specs_text:
        context_lines.append(f"Specs: {specs_text}")
    if payload.raw_notes:
        context_lines.append(f"Seller's notes: {payload.raw_notes}")

    user_prompt = "\n".join(context_lines)

    system_prompt = (
        "You are a copywriter for an electronics e-commerce store called GadgetHub. "
        "Write a product description in 2-3 sentences, based only on the information given. "
        "Be specific and concrete — use the actual specs and seller notes provided. "
        "Avoid generic filler phrases like 'amazing', 'must-have', or 'perfect for everyone'. "
        "Do not invent features, specs, or claims that weren't given to you. "
        "Write in a confident, plain, factual tone — no exclamation marks."
    )

    try:
        description = generate_text(system_prompt, user_prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    return DescriptionResponse(description=description)


VALID_CATEGORIES = [
    "smartphones", "laptops", "audio", "wearables",
    "accessories", "gaming", "smart_home",
]


@router.post("/suggest-category", response_model=CategoryResponse)
def suggest_category(payload: CategoryRequest):
    context = f"Product name: {payload.name}"
    if payload.raw_notes:
        context += f"\nSeller's notes: {payload.raw_notes}"

    system_prompt = (
        "You classify electronics products into exactly one category. "
        f"Valid categories are: {', '.join(VALID_CATEGORIES)}. "
        "Respond with ONLY the category key from that list, nothing else — "
        "no explanation, no punctuation, just the exact category word."
    )

    try:
        raw_output = generate_text(system_prompt, context, model="gpt-4o-mini")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    cleaned = raw_output.strip().lower()

    if cleaned in VALID_CATEGORIES:
        return CategoryResponse(category=cleaned, confidence_note="Matched directly.")

    for valid in VALID_CATEGORIES:
        if valid in cleaned:
            return CategoryResponse(category=valid, confidence_note="Matched via partial text.")

    return CategoryResponse(category="", confidence_note=f"Could not confidently classify (model returned: '{raw_output}').")

from vector_store import search_products
from schemas import SearchRequest, SearchResponse


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest):
    hits = search_products(payload.query, payload.n_results)
    return SearchResponse(results=hits)