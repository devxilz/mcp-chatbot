from sentence_transformers import SentenceTransformer
import torch

model = None

def get_model():
    global model
    if model is None:
        print("Loading embedding model...")

        device = "cuda" if torch.cuda.is_available() else "cpu"

        model = SentenceTransformer("all-MiniLM-L6-v2", device=device)

        print(f"Embedding model loaded on: {device}")

    return model
