"""
Corpus Upload Script for Pinecone Vector Database

This script uploads documents from a JSONL file to your Pinecone vector index.
It uses the same configuration as your RAG service to ensure compatibility.

Usage:
    python upload_corpus.py

The script will:
1. Load documents from auto_finance_corpus.jsonl
2. Convert text to embeddings using your configured model
3. Upload to Pinecone in batches
4. Display progress and completion status
"""

import json
import os
from typing import Optional
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from config import get_settings

def upload_corpus_to_pinecone(
    jsonl_path: str, 
    namespace: Optional[str] = None, 
    batch_size: int = 50
):
    """
    Loads JSONL corpus and uploads into Pinecone vector index.
    
    Args:
        jsonl_path: Path to the JSONL file containing documents
        namespace: Optional namespace to isolate datasets (e.g., "auto_finance")
        batch_size: Number of documents to upload per batch (default: 50)
    
    Raises:
        FileNotFoundError: If the JSONL file doesn't exist
        Exception: If upload fails
    """
    
    # Validate file exists
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"❌ File not found: {jsonl_path}")

    # Load settings from config
    print("🔧 Loading configuration...")
    settings = get_settings()
    
    # Initialize Pinecone client
    print(f"🔌 Connecting to Pinecone (index: {settings.pinecone_index_name})...")
    pc = Pinecone(api_key=settings.pinecone_api_key)
    
    # Initialize embeddings model
    print(f"🤖 Initializing embeddings model ({settings.embedding_model})...")
    embeddings = PineconeEmbeddings(
        model=settings.embedding_model,
        pinecone_api_key=settings.pinecone_api_key
    )
    
    # Initialize vector store
    print("📦 Initializing vector store...")
    docsearch = PineconeVectorStore(
        embedding=embeddings,
        index_name=settings.pinecone_index_name,
        pinecone_api_key=settings.pinecone_api_key,
        text_key="text",
        namespace=namespace
    )
    
    # Load documents from JSONL
    texts = []
    metadatas = []
    ids = []
    
    print(f"\n📥 Loading records from {jsonl_path}...")
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                rec = json.loads(line.strip())
                
                # Extract required fields
                ids.append(rec["id"])
                texts.append(rec["text"])
                
                # Extract metadata (all fields except id and text)
                metadata = {
                    "title": rec.get("title", ""),
                    "category": rec.get("category", ""),
                    "tags": rec.get("tags", []),
                    "source": rec.get("source", "ConsumerFinance"),
                    "effective_date": rec.get("effective_date", "")
                }
                metadatas.append(metadata)
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Skipping invalid JSON on line {line_num}: {e}")
                continue
            except KeyError as e:
                print(f"⚠️  Warning: Missing required field on line {line_num}: {e}")
                continue
    
    total_docs = len(texts)
    print(f"✅ Loaded {total_docs} documents")
    
    if total_docs == 0:
        print("❌ No documents to upload. Exiting.")
        return
    
    # Upload in batches
    print(f"\n📤 Uploading {total_docs} documents to Pinecone in batches of {batch_size}...")
    print(f"   Index: {settings.pinecone_index_name}")
    if namespace:
        print(f"   Namespace: {namespace}")
    print()
    
    total_batches = (total_docs + batch_size - 1) // batch_size
    
    for i in range(0, total_docs, batch_size):
        batch_num = i // batch_size + 1
        batch_texts = texts[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        try:
            # Upload batch to Pinecone
            docsearch.add_texts(
                texts=batch_texts,
                metadatas=batch_metas,
                ids=batch_ids
            )
            
            docs_uploaded = min(i + batch_size, total_docs)
            print(f"   ✅ Batch {batch_num}/{total_batches} complete ({docs_uploaded}/{total_docs} documents)")
            
        except Exception as e:
            print(f"   ❌ Error uploading batch {batch_num}: {e}")
            raise
    
    print(f"\n🎉 Upload complete!")
    print(f"   Total documents uploaded: {total_docs}")
    print(f"   Index: {settings.pinecone_index_name}")
    print(f"   Your RAG service can now use this knowledge base!")


def main():
    """Main execution function"""
    print("=" * 60)
    print("📚 Pinecone Corpus Upload Tool")
    print("=" * 60)
    print()
    
    # Configuration
    jsonl_file = "auto_finance_corpus.jsonl"
    namespace = None  # Set to "auto_finance" if you want to use namespaces
    batch_size = 50
    
    try:
        upload_corpus_to_pinecone(
            jsonl_path=jsonl_file,
            namespace=namespace,
            batch_size=batch_size
        )
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"   Make sure '{jsonl_file}' exists in the current directory.")
        return 1
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        print(f"   Check your Pinecone configuration and try again.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
