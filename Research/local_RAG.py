from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os

class LocalRag:

    def __init__(self, cache_folder = "./Vdataset"):
        self.model =  SentenceTransformer("BAAI/bge-small-en-v1.5", device='cpu', cache_folder= cache_folder)
        self.index = None
        self.chunks =[]
    # making texts to vextor 
    # doc embedding
    def _embed_doc(self,chunks :list[str]):
        texts = ["passage: " + t for t in chunks]
        embedding = self.model.encode(texts, normalize_embeddings = True, show_progress_bar=False)
        return embedding.astype("float32")
    # querry embedding
    def _embed_querry(self, querry : str):
        q = self.model.encode(["querry: " + querry], normalize_embeddings = True, show_progress_bar=False)
        return q.astype("float32")
    #  chunking 
    def chunk_len(self, text , max_chunks = 450, overlap = 80):
        start = 0
        chunks =[]
        if text is None:
            raise ValueError("chunk_len() received None instead of text")
        word = text.split()

        while start < len(word):
            end = max_chunks + start
            chunk = " ".join(word[start:end])
            chunks.append(chunk)

            start = end - overlap
            if start < 0:
                start = 0

        return chunks
    # vectoDB
    def build_index(self, chunks : list[str]):
        if not chunks :
            raise ValueError("No chunks provided")
        vector = self._embed_doc(chunks)
        dim = vector.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vector)

        self.index = index
        self.chunks = chunks
    # searching..
    def search(self, querry: str, top_k=5):
        if self.index is None:
            raise RuntimeError("index not built")
        q = self._embed_querry(querry)
        scores, indices = self.index.search(q, top_k)
        result = []
        for i in indices[0]:
            if i == -1:
                continue
            result.append(self.chunks[i])
        return result
    def save(self, index_path = "rag.index", chunk_path = "rag_chunks.npy"):
        if self.index is None:
            raise RuntimeError("No index to save")
        
        faiss.write_index(self.index, index_path)
        np.save(chunk_path, np.array(self.chunks, dtype=object))
    
    def load(self, index_path = "rag.index", chunk_path = "rag_chunks.npy"):
        if not os.path.exists(index_path):
            raise FileNotFoundError("No such file",index_path)
        
        if not os.path.exists(chunk_path):
            raise FileNotFoundError(f"No such file {chunk_path}")
        self.index = faiss.read_index(index_path)
        self.chunks = np.load(chunk_path, allow_pickle=True).tolist()
        