import json
import os

class SchemaError(Exception):
    pass

def load_schema(file_path):
    """
    Loads and validates a schema from a JSON file.
    
    Args:
        file_path (str): Path to the JSON schema file.
        
    Returns:
        dict: The loaded schema.
        
    Raises:
        SchemaError: If the file is not found, invalid JSON, or invalid structure.
    """
    if not os.path.exists(file_path):
        raise SchemaError("File not found.")
    
    try:
        with open(file_path, 'r') as f:
            schema = json.load(f)
    except json.JSONDecodeError:
        raise SchemaError("Invalid JSON format.")
    except Exception as e:
        raise SchemaError(f"Error reading file: {e}")
        
    if not isinstance(schema, dict):
        raise SchemaError("Invalid schema structure. Top level must be a dictionary.")
        
    for table, columns in schema.items():
        if not isinstance(columns, dict):
            raise SchemaError(f"Invalid schema structure. Table '{table}' must map to a dictionary of columns.")
        for col, type_ in columns.items():
            if type_ not in ("int", "string"):
                raise SchemaError(f"Invalid column type '{type_}' for column '{col}' in table '{table}'. Supported types: 'int', 'string'.")
    
    return schema
