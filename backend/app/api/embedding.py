from fastapi import APIRouter
from app.schemas.embedding import EmbeddingRequest , EmbeddingResponse
from app.services.llm.embedding_service import generate_embedding

router = APIRouter(
    prefix="/embed",
    tags=["Embeddings"]
)

@router.post("/generate", response_model=EmbeddingResponse)
def embed_text(req: EmbeddingRequest):
    vector = generate_embedding(req.text)
    return {"embedding": vector}
