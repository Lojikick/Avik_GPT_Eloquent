from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from dotenv import load_dotenv
import os

load_dotenv()

google_api_key = os.environ.get("GOOGLE_API_KEY")
pinecone_api_key = os.environ.get("PINECONE_API_KEY")

pc = Pinecone(
    api_key=pinecone_api_key,
    environment="us-east-1-aws"
)

model_name = "llama-text-embed-v2"
embeddings = PineconeEmbeddings(
    model=model_name,
    pinecone_api_key=os.environ.get('PINECONE_API_KEY')
)

index = pc.Index("ai-powered-chatbot-challenge")

print("Index Stats:", index.describe_index_stats())

## EXTRACTION CODE ##
# def extract_documents_from_pinecone():
#     documents = []
    
#     stats = index.describe_index_stats()
#     print(f"Total vectors in index: {stats['total_vector_count']}")
    
#     try:
#         dummy_vector = [0.0] * 1024
        
#         results = index.query(
#             vector=dummy_vector,
#             top_k=10000,
#             include_metadata=True
#         )
        
#         print(f"Retrieved {len(results['matches'])} vectors")
        
#         for match in results['matches']:
#             if 'text' in match['metadata']:
#                 documents.append(match['metadata']['text'])
#             elif 'content' in match['metadata']:
#                 documents.append(match['metadata']['content'])
#             else:
#                 print("Warning: No text field found in metadata:", match['metadata'].keys())
    
#     except Exception as e:
#         print(f"Error extracting documents: {e}")
    
#     return documents

# # Extract documents
# extracted_documents = extract_documents_from_pinecone()
# print(f"Extracted {len(extracted_documents)} documents")

# # CONVERT STRINGS TO DOCUMENT OBJECTS - THIS IS THE FIX
# document_objects = [
#     Document(
#         page_content=text, 
#         metadata={"source": f"extracted_{i}", "original_id": f"doc_{i}"}
#     ) 
#     for i, text in enumerate(extracted_documents)
# ]

# print(f"Created {len(document_objects)} Document objects")

# Now this will work
docsearch = PineconeVectorStore(
    # Use Document objects, not strings
    embedding=embeddings,
    index_name="ai-powered-chatbot-challenge",
    text_key="text"
)

retriever = docsearch.as_retriever()

ret_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

llm = ChatGoogleGenerativeAI(
    google_api_key=google_api_key,
    model="gemini-1.5-flash",
    temperature=0.7
)

combined_chain = create_stuff_documents_chain(
    llm, ret_qa_chat_prompt
)

retrieval_chain = create_retrieval_chain(retriever, combined_chain)

query1 = "How do I create a new account?"
query2 = "How do I add money to my account?"

# Test the queries
# answer1_without_knowledge = llm.invoke(query1)
# print("Query 1:", query1)
# print("\nAnswer without knowledge:\n\n", answer1_without_knowledge.content)
# print("\n")

answer1_with_knowledge = retrieval_chain.invoke({"input": query1})
print("Answer with knowledge:\n\n", answer1_with_knowledge['answer'])
print("\nContext used:\n\n", answer1_with_knowledge['context'])
print("\n")



