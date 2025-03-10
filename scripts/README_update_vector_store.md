# Update Vector Store File Attributes

This script allows you to update the attributes of files in an OpenAI Vector Store.

## Prerequisites

- Python 3.7+
- OpenAI API key set in your environment or `.env` file
- Vector store already created using `create_vector_store.py`
- Files already uploaded and added to the vector store

## Usage

```bash
python scripts/update_vector_store_file_attributes.py [OPTIONS]
```

### Options

- `--file-id FILE_ID`: Update a specific file by its ID
- `--all`: Update all files in the vector store
- `--sample N`: Update a sample of N files
- `--attributes JSON_STRING`: JSON string of attributes to set
- `--generate`: Generate attributes using OpenAI based on file content

### Examples

1. Update a specific file with custom attributes:
```bash
python scripts/update_vector_store_file_attributes.py --file-id file-abc123 --attributes '{"document_type": "manual", "topic": "installation", "is_technical": true}'
```

2. Generate attributes for all files using OpenAI:
```bash
python scripts/update_vector_store_file_attributes.py --all --generate
```

3. Update a sample of 5 files with basic attributes:
```bash
python scripts/update_vector_store_file_attributes.py --sample 5
```

## Attribute Types

According to the OpenAI API, attributes can be of the following types:
- String
- Integer
- Float
- Boolean

Example of valid attributes:
```json
{
  "document_type": "manual",
  "page_count": 42,
  "relevance_score": 0.95,
  "is_technical": true
}
```

## API Endpoint

This script uses the following OpenAI API endpoint:
```
POST /v1/vector_stores/{vector_store_id}/files/{file_id}
```

With a request body containing the attributes to update:
```json
{
  "attributes": {
    "key1": "value1",
    "key2": 123,
    "key3": true
  }
}
``` 