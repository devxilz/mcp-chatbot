# from app.utils.model_loder import load_model
from sentence_transformers import SentenceTransformer 
import faiss
import numpy as np
import os


class MemoryEngine:
    def __init__(self,index_path="memory.index"):
        self.index_path = index_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.diemension = self.model.get_sentence_embedding_dimension()

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            print("Index loaded successfully.")
        else:
            self.index = faiss.IndexFlatL2(self.diemension)
            print("New index created.")

    def embed_text(self, text: str) -> np.array:
        vectors = self.model.encode([text])
        return np.array(vectors, dtype=np.float32)

    def add_memory(self, text: str):
        vector = self.embed_text(text)
        self.index.add(vector)
        print(f"Memory added: {text}")   
        print(f"Total memories stored: {self.index.ntotal}")  

        #save after every addition
        self.save()

    def search_memory(self,query:str, k: int=3):
        query_vector = self.embed_text(query)
        distances, indices = self.index.search(query_vector, k)
        return distances, indices

    def save(self):
        faiss.write_index(self.index, self.index_path)
        print(f"Index saved to {self.index_path}")
       
