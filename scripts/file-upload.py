from openai import OpenAI
from dotenv import load_dotenv
import os
import glob
import json
from datetime import datetime

load_dotenv()  # Load environment variables from .env file

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Get all JSON files from the english_chunks directory
chunk_files = glob.glob("english_chunks/*.json")
uploaded_files = []
failed_files = []

# Step 1: Upload files
for chunk_file in chunk_files:
    try:
        file = client.files.create(
            file=open(chunk_file, "rb"),
            purpose="assistants"
        )
        uploaded_files.append({"filename": chunk_file, "file_id": file.id})
        print(f"Successfully uploaded {chunk_file} with file ID: {file.id}")
    except Exception as e:
        error_details = {
            "filename": chunk_file,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        failed_files.append(error_details)
        print(f"Error uploading {chunk_file}: {str(e)}")

# Step 2: Create a vector store from the uploaded files
try:
    file_ids = [file["file_id"] for file in uploaded_files]
    vector_store = client.beta.vector_stores.create(
        name="english_chunks_store",
        file_ids=file_ids
    )
    print(f"Successfully created vector store with ID: {vector_store.id}")
    
    # Save vector store ID for future use
    with open("vector_store_info.json", "w") as f:
        json.dump({"vector_store_id": vector_store.id}, f, indent=2)
        
except Exception as e:
    print(f"Error creating vector store: {str(e)}")

# Save the successful uploads
with open("uploaded_files.json", "w") as f:
    json.dump(uploaded_files, f, indent=2)

# Save the failed uploads with timestamp
if failed_files:
    with open("failed_uploads.json", "w") as f:
        json.dump(failed_files, f, indent=2)

print(f"\nTotal files uploaded successfully: {len(uploaded_files)}")
print(f"Total files failed: {len(failed_files)}")
print("Successful uploads saved to uploaded_files.json")
if failed_files:
    print("Failed uploads saved to failed_uploads.json")
