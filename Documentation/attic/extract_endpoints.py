import json

# Load the OpenAPI spec from file
with open('openapi.json') as f:
    spec = json.load(f)

# Extract and print all routes with their methods
for path, methods in spec.get('paths', {}).items():
    for method in methods:
        print(f"{method.upper()} {path}")
