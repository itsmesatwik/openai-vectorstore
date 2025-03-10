# Document Assistant Chat Application

This is a simple web application that allows you to interact with an OpenAI Assistant that has access to your uploaded documents through a vector store.

<img width="770" alt="image" src="https://github.com/user-attachments/assets/50f7f887-0c15-48d0-af84-2711fa27a9b2" />


## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Documents already uploaded and processed into a vector store

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Run the file upload script to upload your documents and create a vector store:
   ```
   python scripts/file-upload.py
   ```
   This will create a `vector_store_info.json` file with your vector store ID.

## Running the Application

1. Start the Flask application:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Start chatting with the assistant about your documents!

## Vector Store Management

### Listing Vector Stores

You can list all available vector stores using the provided script:

```
python scripts/list-vector-stores.py
```

This will display all vector stores in your account, including their IDs, names, descriptions, creation dates, and associated files.

### Switching Vector Stores

The web application includes a dropdown menu in the header that allows you to:

1. View all available vector stores
2. Select a different vector store to use with the assistant
3. Refresh the list of vector stores

When you switch to a different vector store, the application will:
- Update the vector store ID in `vector_store_info.json`
- Create a new assistant with access to the selected vector store
- Start a new conversation thread

## How It Works

1. The application creates an OpenAI Assistant with access to your vector store
2. When you send a message, it's added to a thread
3. The assistant processes your message and searches through your documents to provide relevant answers
4. The response is displayed in the chat interface

## Files

- `app.py`: The Flask application
- `templates/index.html`: The HTML template for the chat interface
- `static/css/style.css`: CSS styles for the chat interface
- `static/js/script.js`: JavaScript for handling the chat functionality
- `scripts/file-upload.py`: Script for uploading files and creating a vector store
- `scripts/list-vector-stores.py`: Script for listing all vector stores

## Notes

- The assistant and thread IDs are stored in `assistant_info.json` for reuse
- The vector store ID is stored in `vector_store_info.json`
- The application uses the OpenAI Assistants API v2 with the file_search tool 
