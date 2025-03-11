from flask import Flask, render_template, request, jsonify
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load vector store ID
try:
    with open("vector_store_info.json", "r") as f:
        vector_store_info = json.load(f)
        vector_store_id = vector_store_info.get("vector_store_id")
except FileNotFoundError:
    vector_store_id = None
    print("Warning: vector_store_info.json not found. Please run file-upload.py first.")

# Create or get assistant
def get_or_create_assistant():
    # Check if assistant ID is stored
    try:
        with open("assistant_info.json", "r") as f:
            assistant_info = json.load(f)
            assistant_id = assistant_info.get("assistant_id")
            
            # Verify the assistant still exists
            try:
                client.beta.assistants.retrieve(assistant_id)
                return assistant_id
            except:
                print("Assistant not found, creating a new one...")
                pass
    except FileNotFoundError:
        print("No existing assistant found, creating a new one...")
    
    # Create a new assistant
    if not vector_store_id:
        raise ValueError("Vector store ID not found. Please run file-upload.py first.")
    
    assistant = client.beta.assistants.create(
        name="Document Assistant",
        instructions="You are a helpful assistant that can answer questions based on the documents provided in the vector store.",
        model="gpt-4-turbo-preview",
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_store_id]
            }
        }
    )
    
    # Save assistant ID
    with open("assistant_info.json", "w") as f:
        json.dump({"assistant_id": assistant.id}, f, indent=2)
    
    return assistant.id

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/vector-stores', methods=['GET'])
def list_vector_stores():
    try:
        # List all vector stores
        vector_stores = client.beta.vector_stores.list()
        
        # Format the response
        stores_list = []
        for store in vector_stores.data:
            store_data = {
                "id": store.id,
                "name": store.name,
                "created_at": store.created_at
            }
            
            # Add additional fields if they exist
            if hasattr(store, 'bytes'):
                store_data["bytes"] = store.bytes
                
            if hasattr(store, 'file_counts'):
                store_data["file_counts"] = {
                    "in_progress": store.file_counts.in_progress,
                    "completed": store.file_counts.completed,
                    "failed": store.file_counts.failed,
                    "cancelled": store.file_counts.cancelled,
                    "total": store.file_counts.total
                }
                
            stores_list.append(store_data)
        
        return jsonify({
            "vector_stores": stores_list,
            "current_vector_store_id": vector_store_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/set-vector-store', methods=['POST'])
def set_vector_store():
    data = request.json
    new_vector_store_id = data.get('vector_store_id')
    
    if not new_vector_store_id:
        return jsonify({"error": "Missing vector store ID"}), 400
    
    try:
        # Verify the vector store exists
        client.beta.vector_stores.retrieve(new_vector_store_id)
        
        # Save the new vector store ID
        global vector_store_id
        vector_store_id = new_vector_store_id
        
        with open("vector_store_info.json", "w") as f:
            json.dump({"vector_store_id": vector_store_id}, f, indent=2)
        
        # Delete the assistant info so a new one will be created with the new vector store
        if os.path.exists("assistant_info.json"):
            os.remove("assistant_info.json")
        
        return jsonify({
            "success": True,
            "message": "Vector store updated successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/start-thread', methods=['POST'])
def start_thread():
    try:
        # Get or create assistant
        assistant_id = get_or_create_assistant()
        
        # Create a new thread
        thread = client.beta.threads.create()
        
        return jsonify({
            "thread_id": thread.id,
            "assistant_id": assistant_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    thread_id = data.get('thread_id')
    assistant_id = data.get('assistant_id')
    message = data.get('message')
    
    if not thread_id or not assistant_id or not message:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        # Add message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Poll for completion
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return jsonify({"error": f"Run {run_status.status}"}), 500
            
            time.sleep(1)
        
        # Get messages
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        # Get the latest assistant message
        assistant_messages = [
            msg for msg in messages.data 
            if msg.role == "assistant"
        ]
        
        if not assistant_messages:
            return jsonify({"error": "No response from assistant"}), 500
        
        latest_message = assistant_messages[0]
        
        # Extract text content
        message_content = ""
        for content in latest_message.content:
            if content.type == "text":
                message_content += content.text.value
        
        return jsonify({
            "response": message_content
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search-vector-store', methods=['POST'])
def search_vector_store():
    """API endpoint to search the vector store."""
    global vector_store_id
    
    if not vector_store_id:
        return jsonify({"error": "Vector store ID not found"}), 400
    
    data = request.json
    query = data.get('query')
    max_results = data.get('max_results', 10)
    rewrite_query = data.get('rewrite_query', False)
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        # Import the search function directly from the scripts directory
        import os
        import sys
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
        sys.path.insert(0, script_path)
        from search_vector_store import search_vector_store as search_vs
        
        # Ensure max_results is within valid range
        max_results = min(max(1, max_results), 50)
        
        # Set up ranking options if needed
        ranking_options = None
        
        # Perform the search using the imported function
        results = search_vs(
            vector_store_id, 
            query, 
            max_results=max_results,
            filters=None,
            rewrite_query=rewrite_query,
            ranking_options=ranking_options
        )
        
        if not results:
            return jsonify({"error": "Search failed or returned no results"}), 500
        
        # Process the results to ensure they're in a consistent format
        # The search_vector_store.py function returns a dictionary with data array
        if isinstance(results, dict) and 'data' in results:
            # Already in the expected format
            return jsonify(results)
        else:
            # Format the results to match the expected structure
            formatted_results = {
                "search_query": query,
                "data": results if isinstance(results, list) else []
            }
            return jsonify(formatted_results)
    
    except Exception as e:
        print(f"Error searching vector store: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 