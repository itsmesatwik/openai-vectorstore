#!/usr/bin/env python3
import os
import json
import argparse
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_vector_store(vector_store_id, query, top_k=5):
    """Query the vector store and return the top k results."""
    try:
        response = client.beta.vector_stores.query(
            vector_store_id=vector_store_id,
            query=query,
            top_k=top_k
        )
        
        return response.matches
    except Exception as e:
        print(f"Error querying vector store: {e}")
        return []

def display_results(matches):
    """Display the query results in a readable format."""
    if not matches:
        print("No results found.")
        return
    
    print(f"\nFound {len(matches)} results:\n")
    
    for i, match in enumerate(matches, 1):
        print(f"Result {i} (Score: {match.score:.4f}):")
        print(f"File ID: {match.file_id}")
        
        # Display the text content if available
        if hasattr(match, 'text'):
            print(f"Text: {match.text[:200]}..." if len(match.text) > 200 else f"Text: {match.text}")
        
        # Display metadata if available
        if hasattr(match, 'metadata') and match.metadata:
            print("Metadata:")
            for key, value in match.metadata.items():
                print(f"  {key}: {value}")
        
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Query an OpenAI vector store")
    parser.add_argument("vector_store_id", help="The ID of the vector store to query")
    parser.add_argument("query", help="The query to search for")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return (default: 5)")
    
    args = parser.parse_args()
    
    print(f"Querying vector store {args.vector_store_id} with: '{args.query}'")
    
    matches = query_vector_store(args.vector_store_id, args.query, args.top_k)
    display_results(matches)

if __name__ == "__main__":
    main() 