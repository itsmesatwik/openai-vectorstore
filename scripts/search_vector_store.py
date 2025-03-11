#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_vector_store_info():
    """Load the vector store information from the JSON file."""
    try:
        with open("vector_store_info.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: vector_store_info.json not found. Please run create_vector_store.py first.")
        return None

def search_vector_store(vector_store_id, query, max_results=10, filters=None, rewrite_query=False, ranking_options=None):
    """Search the vector store using a curl POST request."""
    try:
        # Prepare the curl command
        api_key = os.getenv("OPENAI_API_KEY")
        url = f"https://api.openai.com/v1/vector_stores/{vector_store_id}/search"
        
        # Build the request payload
        payload = {
            "query": query,
            "max_num_results": max_results
        }
        
        # Add optional parameters if provided
        if filters:
            payload["filters"] = filters
        
        if rewrite_query:
            payload["rewrite_query"] = rewrite_query
            
        if ranking_options:
            payload["ranking_options"] = ranking_options
        
        # Convert payload to JSON string
        payload_json = json.dumps(payload)
        
        # Build the curl command
        curl_command = [
            "curl", url,
            "-X", "POST",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-H", "OpenAI-Beta: assistants=v2",
            "-d", payload_json
        ]
        
        # Execute the curl command
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Curl command failed: {result.stderr}")
            return None
        
        # Parse the response
        try:
            response = json.loads(result.stdout)
            return response
        except json.JSONDecodeError:
            print(f"Failed to parse response: {result.stdout}")
            print(f"Raw response: {result.stdout}")
            return None
            
    except Exception as e:
        print(f"Error searching vector store: {e}")
        return None

def display_search_results(results):
    """Display the search results in a readable format."""
    if not results:
        print("No results found or error occurred.")
        return
    
    print(f"\nSearch Query: {results.get('search_query', 'N/A')}")
    print(f"Number of results: {len(results.get('data', []))}")
    print(f"Has more: {results.get('has_more', False)}")
    
    print("\n=== SEARCH RESULTS ===\n")
    
    for i, item in enumerate(results.get('data', []), 1):
        print(f"Result {i}:")
        print(f"  File ID: {item.get('file_id', 'N/A')}")
        print(f"  Filename: {item.get('filename', 'N/A')}")
        print(f"  Score: {item.get('score', 'N/A')}")
        
        # Display attributes if present
        if 'attributes' in item and item['attributes']:
            print("  Attributes:")
            for key, value in item['attributes'].items():
                print(f"    {key}: {value}")
        
        # Display content if present
        if 'content' in item and item['content']:
            print("  Content:")
            for content_item in item['content']:
                if content_item.get('type') == 'text':
                    # Truncate long text for display
                    text = content_item.get('text', '')
                    if len(text) > 200:
                        text = text[:200] + "..."
                    print(f"    {text}")
        
        print()  # Empty line between results

def main():
    parser = argparse.ArgumentParser(description="Search a vector store")
    parser.add_argument("query", help="The search query")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results (1-50)")
    parser.add_argument("--filter", help="JSON string of filter criteria")
    parser.add_argument("--rewrite-query", action="store_true", help="Enable query rewriting")
    parser.add_argument("--score-threshold", type=float, help="Score threshold (0.0-1.0)")
    parser.add_argument("--ranker", choices=["auto", "default-2024-11-15"], help="Ranker to use")
    
    args = parser.parse_args()
    
    # Load vector store info
    vector_store_info = load_vector_store_info()
    if not vector_store_info:
        return
    
    vector_store_id = vector_store_info["vector_store_id"]
    
    # Parse filter if provided
    filters = None
    if args.filter:
        try:
            filters = json.loads(args.filter)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in --filter")
            return
    
    # Build ranking options if provided
    ranking_options = {}
    if args.ranker:
        ranking_options["ranker"] = args.ranker
    if args.score_threshold is not None:
        if 0.0 <= args.score_threshold <= 1.0:
            ranking_options["score_threshold"] = args.score_threshold
        else:
            print("Error: Score threshold must be between 0.0 and 1.0")
            return
    
    # Only include ranking_options if not empty
    ranking_options = ranking_options if ranking_options else None
    
    # Perform the search
    print(f"Searching vector store {vector_store_id} for: {args.query}")
    results = search_vector_store(
        vector_store_id, 
        args.query, 
        max_results=args.max_results,
        filters=filters,
        rewrite_query=args.rewrite_query,
        ranking_options=ranking_options
    )
    
    # Display the results
    display_search_results(results)

if __name__ == "__main__":
    main() 