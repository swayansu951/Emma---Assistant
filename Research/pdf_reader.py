import gc
import hashlib
import re
import time
from langchain_community.document_loaders import PyPDFDirectoryLoader
from pathlib import Path
import subprocess,os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.embeddings import BedrockEmbeddings, OllamaEmbeddings
from langchain_community.vectorstores.chroma import Chroma
import ollama
import shutil
from langchain.agents import create_agent
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from torch import chunk
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Voice.assistant_voice import TTSEngine


prefix = '.pdf'
class PDFREADER:
    def __init__(self):
        # if os.path.exists("pdf_vector_db"):
        #     pass
        self.embedding = OllamaEmbeddings(model="nomic-embed-text")

        self.db = Chroma(persist_directory="pdf_vector_db", 
                         embedding_function= self.embedding
                         )
    # def embedding_parallel(self, chunks):
    #     def embed(chunk):
    #         return self.embedding.embed_query(chunk.page_content)
        
    #     with ThreadPoolExecutor(max_workers=5) as executor:
    #         embeddings = list(executor.map(embed, chunks))

    #     return embeddings
    
    # find the path in desktop
    def _search_file(self, file_name):

        desktop_app = Path.home()/ "Desktop"
        apps = [app for app in desktop_app.iterdir() if app.is_file()]

        for p in apps:
            if p.name.lower() == file_name.lower():
                full_path = p
                return p
        raise FileNotFoundError(f"No such file: {file_name} in desktop")
    
    # generates chunk if present 
    def _generate_chunk_id(self, chunk):
        """Generate a unique ID for a chunk based on its content and metadata"""

        # Create a unique fingerprint of the chunk
        file_path = Path(chunk.metadata.get('source_path', ''))
        if file_path.exists():
            file_version = f"{file_path.stat().st_size}_{file_path.stat().st_mtime}"
        else:
            file_version = "unknown"
        
        content_to_hash = f"{chunk.page_content}_{file_version}_{chunk.metadata.get('page', 0)}"
        return hashlib.md5(content_to_hash.encode()).hexdigest()[:16]
    
    #load the pdf
    def _pdf_load(self, file_name):

        pdf_path = self._search_file(file_name)
        loader = PyPDFDirectoryLoader(str(pdf_path.parent), glob=file_name )
        documents = loader.load()
        
        # Enhance metadata with source info
        for doc in documents:
            doc.metadata.update({
                "source_file": pdf_path.name,
                "source_path": str(pdf_path)
            })
        return documents
    
    # text splitter
    def _pdf_TextSplitter(self, documents : list[Document]):
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120,
                                                       length_function = len,
                                                       is_separator_regex=False)
        
        chunks = text_splitter.split_documents(documents)
        
        # Add unique IDs to each chunk
        for chunk in chunks:
            chunk.metadata['chunk_id'] = self._generate_chunk_id(chunk)
        
        return chunks
    # embedding for pdf
    def _pdf_embedding(self):
        return self.embedding
        # return OllamaEmbeddings(model="nomic-embed-text")
    
    # add to vectorDB
    def add_to_vectorDB(self, chunks :list[Document]):
        
        existing_items = self.db.get(include=['metadatas'])

        existing_ids = set(metadata.get('chunk_id')
                           for metadata in existing_items['metadatas'] 
                          if metadata and 'chunk_id' in metadata)
        
        new_chunks = [chunk for chunk in chunks 
                     if chunk.metadata.get('chunk_id') not in existing_ids
                     ]
        
        if not new_chunks:
            print("[+] No new chunks to add.")
            return 
        batch_size = 32

        batches = [new_chunks[i:i + batch_size] 
                   for i in range(0, len(new_chunks), batch_size)
                   ]
        def process_batches(batch):
            ids = [f"chunk_{chunk.metadata['chunk_id']}" for chunk in batch
                   ]
            self.db.add_documents(batch, ids=ids)
            print(f"[+] Added batch of {len(batch)} chunks to database")
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(process_batches, batches)
        for batch in batches:
            process_batches(batch)

    #update the DB with new file
    def update_DB(self,file_name):
        documents = self._pdf_load(file_name)
        chunks = self._pdf_TextSplitter(documents)
        self.add_to_vectorDB(chunks)
    
    
class TEST_RAG():
    prompt = f"""
        Answer the question using the context below. If the answer is not found in the context, say "I don't know".
        Context:
        {"context"}
        Question:
        {"user_input"}
        """
    def __init__(self, reader = None):
        if reader is None:
            reader = PDFREADER()
        self.reader = reader
        self.messages = [{'role': 'system', 'content': self.prompt}]

    def delete_DB(self):
        db_path = "pdf_vector_db"
    
        if os.path.exists(db_path):
            try:
                client = self.reader.db._client
                
                if self.reader.db:
                   del self.reader.db  
                del client    
                
                gc.collect()
                time.sleep(2)
          
                shutil.rmtree(db_path)
                print("[+] Vector database deleted.")
            except Exception as e:
                print(f"[?] Error occurred while deleting vector database: {e}")
        else:
            print("[-] No vector database found to delete.")

    def reset_DB(self):

        self.delete_DB()

        os.makedirs("pdf_vector_db", exist_ok=True)
        self.reader.db = Chroma(persist_directory="pdf_vector_db", 
                         embedding_function=self.reader._pdf_embedding()
                         )    

    def test_pdf_reader(self, file_name):
        
        update = self.reader.update_DB(file_name)
    
    def retrieve_context(self, query: str) -> str:
        """Retrieve information to help answer a query."""

        retrieved_docs = self.reader.db.similarity_search(query, k=5)

        serialized = "\n\n".join(
            f"Source: {doc.metadata}\nContent: {doc.page_content}"
            for doc in retrieved_docs
            )
        return serialized
    
    def starts(self, user_input: str,pdf: str):

        context = self.retrieve_context(user_input)

        prompt = f"""
        Answer the question using the context below. If the answer is not found in the context, say "I don't know".
        Context:
        {context}
        Question:
        {user_input}
        """
        self.messages.append({"role":"user","content":prompt})

        response = ollama.chat(model='llama3.1:8b-instruct-q5_K_S', messages=self.messages, stream=True, options={"num_thread":5,"keep_alive":"1m"})
        full_response = ""
        sentence_buffer = ""

        for chunk in response:
            content = chunk['message']['content']
            full_response += content
            sentence_buffer += content

            if any(p in content for p in [".","!","?","*","\n"]):
                    text_to_speak = re.sub(r'\[.*?\]', '', sentence_buffer).strip()

                    if text_to_speak:
                        yield str(text_to_speak)
                    sentence_buffer= ""

        if sentence_buffer.strip():
                final_text = re.sub(r'\[.*?\]', '', sentence_buffer).strip()
                if final_text:
                    yield final_text
        
def Researcher():
    reader = PDFREADER()
    voice = TTSEngine()
    files = []
    if not os.path.exists("pdf_vector_db"):
        os.makedirs("pdf_vector_db")
    rag = TEST_RAG(reader)
    while True:
        user = input("\nWant to load a new PDF? (yes./no.)\n")
        try:
            if (text := input("\nEnter your question (or 'bye' to exit): \n")).strip():
                if "yes" in user.strip().lower() or len(files) == 0:
                    pdf = input("\nEnter the pdf file name with .pdf extension and press enter to start: \n")
                    cmd = pdf.strip().lower()

                    if cmd.endswith('.pdf'):
                        rag.test_pdf_reader(cmd)
                        print("PDF processed and added to vector database.")
                    else:
                        print(f"invalid file name '{cmd}', might have missed the .pdf extension or the file is not in desktop, please try again.")
                    files.append(cmd)
                    print(f"PDF '{cmd}' loaded and processed.")
            else:
                if "no" in user.strip().lower():
                        vector_db = reader.db              
                else:
                    pdf = files[0]  # Use the first PDF file in the list
                    cmd = pdf.strip().lower()

            user_text = ""
            user_text = text.strip()
            # if "bye" in user_text.lower():
            #     print("Goodbye!")
            #     break
            if "delete database" in user_text:
                confirm = input("Are you sure you want to delete the vector database? (yes/no)")
                if confirm.strip().lower() == "yes":
                    rag.reset_DB()
                    print("[+] Vector database reset and ready for new data.")
                    continue
                else:
                    print("Database deletion cancelled.")
                
            if user_text:
                if "bye" in user_text.lower():
                    print("Researcher : catch you soon sir!")
                    voice.speak("catch you soon sir!")  
                    break 
                
                print("Researcher : ",end="",flush=True)
                
                response = rag.starts(user_input= user_text, pdf= cmd)
                # voice\
                spoken =False
                for sentence in response:
                    spoken = True
                    print(sentence, end=" ", flush=True)
                    voice.speak(sentence)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    Researcher()