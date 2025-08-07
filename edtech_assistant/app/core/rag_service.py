# FILE: app/core/rag_service.py

import os
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate

VECTOR_STORE_PATH = "./chroma_db"
KNOWLEDGE_BASE_PATH = "./knowledge_base"

class RAGService:
    def __init__(self):
        self.llm = ChatOllama(model="llama3")
        self.embeddings = OllamaEmbeddings(model="llama3")
        if os.path.exists(VECTOR_STORE_PATH):
            print("INFO: Loading existing vector store from disk.")
            self.vector_store = Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=self.embeddings)
        else:
            print("INFO: Creating new vector store. This may take a moment...")
            loader = DirectoryLoader(KNOWLEDGE_BASE_PATH, glob="*.txt", show_progress=True)
            docs = loader.load()
            if not docs:
                raise ValueError(f"No documents found in {KNOWLEDGE_BASE_PATH}.")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            print(f"INFO: Creating embeddings for {len(splits)} document splits.")
            self.vector_store = Chroma.from_documents(documents=splits, embedding=self.embeddings, persist_directory=VECTOR_STORE_PATH)
            print("INFO: Vector store created and persisted.")
        self.retriever = self.vector_store.as_retriever()
        prompt_template = """
        You are a helpful EdTech assistant...
        Context: {context}
        Question: {input}
        Answer:
        """
        prompt = PromptTemplate.from_template(prompt_template)
        self.question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)

    def query(self, question: str) -> str:
        print(f"INFO: RAG Service received query: '{question}'")
        response = self.rag_chain.invoke({"input": question})
        print("INFO: RAG Service generated a response.")
        return response["answer"]