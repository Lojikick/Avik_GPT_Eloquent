from pymongo import MongoClient
from config import get_settings
import os
def test_connection():
    try:
        settings = get_settings()
        client = MongoClient(settings.mongodb_uri)
        # mongo_uri_key = os.environ.get("MONGODB_URI")
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # Test database access
        db = client.chatbot_db
        collection = db.test_collection
        
        # Insert a test document
        result = collection.insert_one({"test": "Hello from Python!", "timestamp": "2025-01-01"})
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Read it back
        doc = collection.find_one({"test": "Hello from Python!"})
        print(f"✅ Found document: {doc}")
        
        # Clean up
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document cleaned up")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()