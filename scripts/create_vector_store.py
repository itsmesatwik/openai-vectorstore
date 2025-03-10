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

def create_vector_store(name):
    """Create a new vector store."""
    try:
        response = client.beta.vector_stores.create(
            name=name
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
    vector_store_name = "verkada_english_chunks_store"
    
    vector_store_id = create_vector_store(vector_store_name)
    
    if vector_store_id:
        # Add files to the vector store
        add_files_to_vector_store(vector_store_id, file_ids)
        print(f"Vector store creation complete. Vector Store ID: {vector_store_id}")
        
        # Save the vector store ID to a file for future reference
        store_info = {"vector_store_id": vector_store_id, "name": vector_store_name}
        
        # Try to get additional details about the vector store
        try:
            details = client.beta.vector_stores.retrieve(vector_store_id=vector_store_id)
            if hasattr(details, 'bytes'):
                store_info["bytes"] = details.bytes
            if hasattr(details, 'file_counts'):
                store_info["file_counts"] = {
                    "total": details.file_counts.total,
                    "completed": details.file_counts.completed,
                    "in_progress": details.file_counts.in_progress,
                    "failed": details.file_counts.failed,
                    "cancelled": details.file_counts.cancelled
                }
        except Exception as e:
            print(f"Warning: Could not retrieve additional details: {e}")
        
        with open("vector_store_info.json", "w") as f:
            json.dump(store_info, f, indent=2)
        print(f"Vector store info saved to vector_store_info.json")
    else:
        print("Failed to create vector store.")

if __name__ == "__main__":
    main() 