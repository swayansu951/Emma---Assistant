from Research.local_RAG import LocalRag
# from Research.web_RAG import
from pathlib import Path


# class Rounting:
#     def routing(self,file_text, user_query, chunk_text):
        
#             rag = LocalRag()
#             chunks = chunk_text(file_text)
#             rag.build_index(chunks)
#             contexts = rag.search(user_query, top_k=5)
class LRAG:
    def read_file(self, file_name:str) -> str :
        desktop_app = Path.home()/ "Desktop"
        apps = [app for app in desktop_app.iterdir() if app.is_file()]
        full_path = "C:\\Users\\swaya\\Desktop\\" + file_name+ ".txt"
        
        print(f"searching in : {desktop_app}")
        print(f"requested file: {file_name}")
        print("Available files:", [p.name for p in apps])
        
        for f in apps:
            print("-", f.name)
        full_p = None
        for f in apps:
            if f.is_file() and f.name.lower() == file_name.lower():
                full_p = f
                break
        if full_p is None:
            print("file name not matched")
            return None
        
        try:

            with open(full_path, 'r', encoding="utf-8") as f:
                text = f.read().strip()
                if not text:
                    return None
                return text
            
        except Exception as e:
            print(f"Error : {e}")
            return None

    def insert_rag(self, file_name, rag = LocalRag()):
        
        text = self.read_file(file_name)
        if text is None:
            raise ValueError("file could not be read or empty")
        chunks = rag.chunk_len(text)
        rag.build_index(chunks)
        rag.save()
        print(f'inseted {len(chunks)} chunks into RAG')
        return True
    @staticmethod
    def _should_use_rag(query : str) -> bool:
        q= query.lower()
        examples = ["research",
                    "read file",
                    "from file",
                    "use my file",
                    "according to the file",
                    "from documents"]
        return any(k in q for k in examples)
