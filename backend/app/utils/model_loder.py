from sentence_transformers import SentenceTransformer

model = None

def get_model():
    global model
    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda" if SentenceTransformer()._get_device() == "cuda" else "cpu")
        print("Embedding model loaded successfully.")
    return model
