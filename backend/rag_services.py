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


class RAGService:
    """
    Retrieval-Augmented Generation (RAG) Service
    
    Combines vector search with language models to provide contextually relevant responses.
    Flow: User Query → Vector Search → Retrieve Context → Generate Response with Context
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all RAG system components in proper order"""
        
        # 1. Initialize Pinecone client for vector database operations
        self.pc = Pinecone(
            api_key=self.settings.pinecone_api_key
        )
                
        # 2. Initialize embeddings model - converts text to vectors
        # Uses Pinecone's embedding service with configured model (llama-text-embed-v2)
        self.embeddings = PineconeEmbeddings(
            model=self.settings.embedding_model,
            pinecone_api_key=self.settings.pinecone_api_key
        )
                
        # 3. Initialize vector store - manages document storage and retrieval
        self.docsearch = PineconeVectorStore(
            embedding=self.embeddings,                          # Embedding function
            index_name=self.settings.pinecone_index_name,      # Pinecone index name
            pinecone_api_key=self.settings.pinecone_api_key,   # Authentication
            text_key="text"                                     # Field name for document text
        )
                
        # 4. Create retriever - handles similarity search for relevant documents
        self.retriever = self.docsearch.as_retriever()
                
        # 5. Initialize Large Language Model (LLM) - generates responses
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=self.settings.google_api_key,
            model=self.settings.llm_model,                     # gemini-1.5-flash
            temperature=self.settings.llm_temperature          # Controls response creativity (0.7)
        )
                
        # 6. Initialize LangChain chains - orchestrates RAG workflow
        
        # Pull pre-built prompt template for retrieval-based Q&A with chat history
        self.ret_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
        
        # Create document combination chain - formats retrieved docs for LLM
        self.combined_chain = create_stuff_documents_chain(
            self.llm, self.ret_qa_chat_prompt
        )
        
        # Create full retrieval chain - combines retrieval + generation
        self.retrieval_chain = create_retrieval_chain(
            self.retriever, self.combined_chain
        )
        
    def get_response(self, query: str, session_messages: list) -> dict:
        """
        Main RAG pipeline method
        
        Args:
            query: User's current question/message
            session_messages: Previous conversation history as LangChain messages
            
        Returns:
            dict: Contains AI response and retrieved context documents
            
        Workflow:
        1. Convert query to vector embedding
        2. Search vector database for similar documents
        3. Retrieve relevant context documents
        4. Combine context + chat history + current query
        5. Generate response using LLM with full context
        """
        try:
            # Invoke the complete RAG chain
            answer = self.retrieval_chain.invoke({
                "input": query,                    # Current user question
                "chat_history": session_messages  # Previous conversation for context
            })
            
            return {
                "answer": answer["answer"],                    # Generated response
                "context": answer.get("context", [])          # Retrieved documents used
            }
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")

# Singleton pattern - ensures only one RAG service instance exists
@lru_cache()
def get_rag_service():
    """
    Factory function that returns cached RAG service instance
    
    Benefits:
    - Prevents expensive re-initialization of models and connections
    - Ensures consistent service state across requests
    - Improves API response times after first initialization
    """
    return RAGService()