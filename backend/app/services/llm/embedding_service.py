from app.utils.model_loder import get_model

def generate_embedding(text: str):
    model = get_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()
