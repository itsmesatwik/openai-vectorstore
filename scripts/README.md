# Vector Store Scripts

This directory contains scripts for working with OpenAI's Vector Stores API.

## Prerequisites

- Python 3.6+
- OpenAI API key set in the `.env` file
- Required Python packages: `openai`, `python-dotenv`

## Available Scripts

### 1. Create Vector Store

Creates a new vector store and adds files from `uploaded_files.json` to it.

```bash
./create_vector_store.py
```

This script will:
1. Read the file IDs from `uploaded_files.json`
2. Create a new vector store named "english_documents_store"
3. Add all the files to the vector store in batches
4. Print the vector store ID upon completion

### 2. Query Vector Store

Queries a vector store with a specified query and returns the top results.

```bash
./query_vector_store.py <vector_store_id> "<your query>" [--top-k <number>]
```

Arguments:
- `vector_store_id`: The ID of the vector store to query (required)
- `query`: The search query (required)
- `--top-k`: Number of results to return (optional, default: 5)

Example:
```bash
./query_vector_store.py vs_abc123 "What are the features of Verkada Guest?"
```

### 3. List Vector Stores

Lists all vector stores in your account with their details.

```bash
./list_vector_stores.py
```

This script will display:
- Vector store IDs
- Names
- Descriptions
- Creation dates
- File counts

## Example Workflow

1. Create a vector store:
   ```bash
   ./create_vector_store.py
   ```

2. Note the vector store ID from the output (e.g., `vs_abc123`)

3. Query the vector store:
   ```bash
   ./query_vector_store.py vs_abc123 "What are the latest product features?"
   ```

4. List all vector stores:
   ```bash
   ./list_vector_stores.py
   ```

## Notes

- The scripts handle errors gracefully and provide informative messages.
- Files are added to the vector store in batches to avoid rate limits.
- The query results include scores and metadata when available. 