import chromadb
from chromadb.utils import embedding_functions

# Persistent storage — the vector index survives restarts, saved to disk
client = chromadb.PersistentClient(path="./chroma_data")

# All-MiniLM-L6-v2: a small, fast, free embedding model that runs locally
# (no API calls needed just to generate embeddings)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="products",
    embedding_function=embedding_fn,
)


def index_products(products: list[dict]):
    """Rebuild the product vector index from scratch."""
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    ids = []
    documents = []
    metadatas = []

    for p in products:
        text = f"{p['name']} by {p.get('brand', '')}. {p.get('category_display', '')}. {p.get('description') or p.get('raw_notes') or ''}"
        ids.append(str(p["id"]))
        documents.append(text)
        metadatas.append({
            "name": p["name"],
            "price": p["price"],
            "category": p.get("category", ""),
            "in_stock": p["in_stock"],
        })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def search_products(query: str, n_results: int = 5):
    results = collection.query(query_texts=[query], n_results=n_results)

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "product_id": int(results["ids"][0][i]),
            "name": results["metadatas"][0][i]["name"],
            "price": results["metadatas"][0][i]["price"],
            "category": results["metadatas"][0][i]["category"],
            "in_stock": results["metadatas"][0][i]["in_stock"],
        })
    return hits