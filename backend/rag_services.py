# services.py
from functools import lru_cache
from typing import List
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain_core.embeddings import Embeddings
from langchain_pinecone import PineconeEmbeddings
from config import get_settings


# Custom Pinecone Embeddings class
# class PineconeEmbeddings(Embeddings):
#     def __init__(self, model: str, pinecone_api_key: str):
#         self.pc = Pinecone(api_key=pinecone_api_key)
#         self.model = model
    
#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         response = self.pc.inference.embed(
#             model=self.model,
#             inputs=texts,
#             parameters={"input_type": "passage"}
#         )
#         return [item.values for item in response.data]
    
#     def embed_query(self, text: str) -> List[float]:
#         response = self.pc.inference.embed(
#             model=self.model,
#             inputs=[text],
#             parameters={"input_type": "query"}
#         )
#         return response.data[0].values


class RAGService:
    def __init__(self):
        self.settings = get_settings()
        self._initialize_components()
        
    def _initialize_components(self):
        # Initialize Pinecone
        self.pc = Pinecone(
            api_key=self.settings.pinecone_api_key
        )
                
        # Initialize embeddings with custom PineconeEmbeddings
        self.embeddings = PineconeEmbeddings(
            model=self.settings.embedding_model,
            pinecone_api_key=self.settings.pinecone_api_key
        )
                
        # Initialize vector store
        self.docsearch = PineconeVectorStore(
            embedding=self.embeddings,
            index_name=self.settings.pinecone_index_name,
            pinecone_api_key=self.settings.pinecone_api_key,
            text_key="text"
        )
                
        # Initialize retriever
        self.retriever = self.docsearch.as_retriever()
                
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=self.settings.google_api_key,
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature
        )
                
        # Initialize chains
        self.ret_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
        self.combined_chain = create_stuff_documents_chain(
            self.llm, self.ret_qa_chat_prompt
        )
        self.retrieval_chain = create_retrieval_chain(
            self.retriever, self.combined_chain
        )
        
    def get_response(self, query: str, session_messages: list) -> dict:
        """Get response from RAG system"""
        try:
            answer = self.retrieval_chain.invoke({"input": query, "chat_history": session_messages})
            return {"answer": answer["answer"], "context": answer.get("context", [])}
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")

@lru_cache()
def get_rag_service():
    """Singleton pattern for RAG service"""
    return RAGService()