from fastapi import FastAPI
from routers import products,chat
app = FastAPI()

app.include_router(products.router)
app.include_router(chat.router)

@app.get("/")
def get_root():
    return {"AI service":"running"}