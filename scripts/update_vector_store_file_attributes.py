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

def load_vector_store_info():
    """Load the vector store information from the JSON file."""
    try:
        with open("vector_store_info.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: vector_store_info.json not found. Please run create_vector_store.py first.")
        return None

def load_uploaded_files():
    """Load the uploaded files from the JSON file."""
    try:
        with open("uploaded_files.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: uploaded_files.json not found.")
        return None

def get_file_attributes_from_openai(file_content):
    """Generate attributes for a file using OpenAI API."""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes document content and extracts key attributes."},
                {"role": "user", "content": f"Based on the following content, generate a JSON dictionary of attributes that describe this document. Include attributes like 'document_type', 'topic', 'sentiment', 'complexity_level', 'is_technical', etc. Content: {file_content[:4000]}..."}
            ],
            response_format={"type": "json_object"}
        )
        
        # Extract the JSON from the response
        attributes_json = response.choices[0].message.content
        attributes = json.loads(attributes_json)
        
        return attributes
    except Exception as e:
        print(f"Error generating attributes with OpenAI: {e}")
        return {}

def update_file_attributes(vector_store_id, file_id, attributes):
    """Update the attributes of a file in the vector store."""
    try:
        # Prepare the curl command
        api_key = os.getenv("OPENAI_API_KEY")
        url = f"https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}"
        
        # Convert attributes to JSON string
        attributes_json = json.dumps({"attributes": attributes})
        
        # Build the curl command
        curl_command = [
            "curl", url,
            "-X", "POST",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-H", "OpenAI-Beta: assistants=v2",
            "-d", attributes_json
        ]
        
        # Execute the curl command
        import subprocess
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
            return None
            
    except Exception as e:
        print(f"Error updating file attributes: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Update attributes for vector store files")
    parser.add_argument("--file-id", help="Specific file ID to update (optional)")
    parser.add_argument("--all", action="store_true", help="Update all files in the vector store")
    parser.add_argument("--sample", type=int, help="Update a sample of N files")
    parser.add_argument("--attributes", help="JSON string of attributes to set (optional)")
    parser.add_argument("--generate", action="store_true", help="Generate attributes using OpenAI")
    
    args = parser.parse_args()
    
    # Load vector store info
    vector_store_info = load_vector_store_info()
    if not vector_store_info:
        return
    
    vector_store_id = vector_store_info["vector_store_id"]
    
    # Load uploaded files
    uploaded_files = load_uploaded_files()
    if not uploaded_files:
        return
    
    # Determine which files to update
    files_to_update = []
    
    if args.file_id:
        # Find the file in the uploaded files list
        file_info = next((f for f in uploaded_files if f["file_id"] == args.file_id), None)
        if file_info:
            files_to_update.append(file_info)
        else:
            print(f"Error: File ID {args.file_id} not found in uploaded_files.json")
            return
    elif args.all:
        files_to_update = uploaded_files
    elif args.sample:
        sample_size = min(args.sample, len(uploaded_files))
        files_to_update = uploaded_files[:sample_size]
    else:
        print("Error: Please specify --file-id, --all, or --sample")
        return
    
    # Process each file
    for file_info in files_to_update:
        file_id = file_info["file_id"]
        filename = file_info["filename"]
        
        print(f"Processing file: {filename} (ID: {file_id})")
        
        # Determine attributes to set
        if args.attributes:
            try:
                attributes = json.loads(args.attributes)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in --attributes")
                continue
        elif args.generate:
            # Try to read the file content to generate attributes
            try:
                with open(filename, "r") as f:
                    file_content = f.read()
                attributes = get_file_attributes_from_openai(file_content)
            except FileNotFoundError:
                print(f"Warning: Could not find file {filename} locally. Using basic attributes.")
                attributes = {
                    "document_type": "unknown",
                    "processed": True,
                    "filename": os.path.basename(filename)
                }
        else:
            # Use basic attributes
            attributes = {
                "processed": True,
                "filename": os.path.basename(filename)
            }
        
        # Update the file attributes
        print(f"Setting attributes: {json.dumps(attributes, indent=2)}")
        response = update_file_attributes(vector_store_id, file_id, attributes)
        
        if response:
            print(f"Successfully updated attributes for file: {filename}")
        else:
            print(f"Failed to update attributes for file: {filename}")
    
    print("Attribute update process complete.")

if __name__ == "__main__":
    main() 