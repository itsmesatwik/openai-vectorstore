#!/usr/bin/env python3
import os
import json
import time
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_uploaded_files():
    """Load the uploaded files from the JSON file."""
    with open("uploaded_files.json", "r") as f:
        return json.load(f)

def create_vector_store(name, description):
    """Create a new vector store."""
    try:
        response = client.beta.vector_stores.create(
            name=name,
            description=description
        )
        print(f"Vector store created: {response.id}")
        return response.id
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def add_files_to_vector_store(vector_store_id, file_ids):
    """Add files to the vector store."""
    try:
        # Add files in batches to avoid rate limits
        batch_size = 10
        total_files = len(file_ids)
        
        for i in range(0, total_files, batch_size):
            batch = file_ids[i:i+batch_size]
            print(f"Adding batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size}...")
            
            response = client.beta.vector_stores.file_batches.create(
                vector_store_id=vector_store_id,
                file_ids=batch
            )
            
            print(f"Batch {i//batch_size + 1} added: {response.id}")
            
            # Sleep to avoid rate limits
            if i + batch_size < total_files:
                time.sleep(2)
    
    except Exception as e:
        print(f"Error adding files to vector store: {e}")

def main():
    # Load the uploaded files
    uploaded_files = load_uploaded_files()
    
    # Extract file IDs
    file_ids = [file_info["file_id"] for file_info in uploaded_files]
    
    print(f"Found {len(file_ids)} files to add to the vector store.")
    
    # Create a vector store
    vector_store_name = "english_documents_store"
    vector_store_description = "Vector store containing English document chunks"
    
    vector_store_id = create_vector_store(vector_store_name, vector_store_description)
    
    if vector_store_id:
        # Add files to the vector store
        add_files_to_vector_store(vector_store_id, file_ids)
        print(f"Vector store creation complete. Vector Store ID: {vector_store_id}")
    else:
        print("Failed to create vector store.")

if __name__ == "__main__":
    main() 