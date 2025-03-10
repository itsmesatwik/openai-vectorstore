#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def list_vector_stores():
    """List all vector stores."""
    try:
        response = client.beta.vector_stores.list()
        return response.data
    except Exception as e:
        print(f"Error listing vector stores: {e}")
        return []

def get_vector_store_details(vector_store_id):
    """Get details for a specific vector store."""
    try:
        response = client.beta.vector_stores.retrieve(vector_store_id=vector_store_id)
        return response
    except Exception as e:
        print(f"Error retrieving vector store details: {e}")
        return None

def display_vector_stores(vector_stores):
    """Display vector stores in a readable format."""
    if not vector_stores:
        print("No vector stores found.")
        return
    
    print(f"\nFound {len(vector_stores)} vector stores:\n")
    
    for i, store in enumerate(vector_stores, 1):
        print(f"Vector Store {i}:")
        print(f"  ID: {store.id}")
        print(f"  Name: {store.name}")
        print(f"  Description: {store.description}")
        print(f"  Created at: {store.created_at}")
        
        # Get more details for this vector store
        details = get_vector_store_details(store.id)
        if details and hasattr(details, 'file_count'):
            print(f"  File count: {details.file_count}")
        
        print("-" * 80)

def main():
    print("Listing all vector stores...")
    vector_stores = list_vector_stores()
    display_vector_stores(vector_stores)

if __name__ == "__main__":
    main() 