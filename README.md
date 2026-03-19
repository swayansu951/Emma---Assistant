# ZENITH

A helpfull desktop assistant that can perform all basic tasks for you on a single command.

# TOOLS

for sending message just say/type send message <"throught_which"> to <"to whome"> that <"message">.

for opening app just say/type 
open app <"app_name">.

also support closing the same as opening 
*use close instead of open.

searching for web, say/type 
search web <"content">.

*also it has pdf reading function & web crawling function but it's under development.

*it's under development 

# RAG 1.0 – Simple PDF Retrieval Augmented Generation

Beside making assistant, I worked for making advanced RAG system. *also overview RAG4.0 repo.

This project implements a **basic Retrieval Augmented Generation (RAG) system** designed to answer questions from **PDF documents**.

The system reads PDF files, converts them into embeddings, stores them in a vector database, and retrieves relevant sections to help an LLM generate accurate answers.

This is the **first stage** of a larger AI assistant architecture currently under development.

---

# 🚀 Features

* PDF document ingestion
* Automatic text chunking
* Vector embedding generation
* Vector database storage
* Semantic similarity search
* Context-aware answer generation using an LLM

Currently supports **PDF documents only**.

---

# 🧠 How It Works

The system follows a simple RAG pipeline:

```
PDF Documents
     │
     ▼
Text Extraction
     │
     ▼
Text Chunking
     │
     ▼
Embedding Generation
     │
     ▼
Vector Database Storage
     │
     ▼
User Query
     │
     ▼
Similarity Search
     │
     ▼
Retrieve Relevant Chunks
     │
     ▼
LLM Generates Answer
```

---

# 📂 Project Structure

```
project/ 
│
├── vector_db
|        
├── Research
|       │   
|       └── pdf_reader.py
|
└── main.py
```

---

# ⚙️ Technologies Used

| Component       | Tool                           |
| --------------- | ------------------------------ |
| Language        | Python                         |
| PDF Loader      | LangChain PDF Loader           |
| Text Splitting  | RecursiveCharacterTextSplitter |
| Embeddings      | Sentence Transformers          |
| Vector Database | ChromaDB                       |
| LLM             | Local LLM                      |

---

# 📥 How It Works (Step by Step)

### 1️⃣ Load PDFs

The system scans a directory containing PDF documents.

### 2️⃣ Extract Text

Text is extracted from each PDF.

### 3️⃣ Chunk the Text

Large documents are split into smaller chunks for better retrieval.

### 4️⃣ Generate Embeddings

Each chunk is converted into a vector embedding.

### 5️⃣ Store in Vector Database

Embeddings are stored in a vector database.

### 6️⃣ Query the System

When a user asks a question:

* The query is embedded
* Similar chunks are retrieved
* The retrieved context is sent to the LLM
* The LLM generates an answer based on the document content

---

# 🧪 Current Status

✅ Basic RAG pipeline completed
✅ PDF document ingestion working
❌ Assistant integration not yet implemented

The next step is integrating this system into a **local AI assistant**.

---

# 🔮 Planned Improvements

Future upgrades planned for this project:

* Assistant integration
* Multi-document handling
* Hybrid retrieval (vector + keyword)
* Re-ranking models
* Multi-layer RAG architecture

---

# 🎯 Purpose

This project serves as the **foundation for building advanced RAG systems**, eventually evolving into:

* RAG 2.0 (CLM-based architecture)
* RAG 3.0 (intelligent routing)
* RAG 4.0 (multi-layer hybrid retrieval)

---

# 👨‍💻 Author

Developed as part of a learning and experimentation project focused on **building advanced Retrieval Augmented Generation systems from scratch**.
