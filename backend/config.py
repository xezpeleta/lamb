import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'false'
LAMB_HOST = os.getenv('PIPELINES_HOST', 'http://localhost:9099')
# Get the token from environment and strip any whitespace
pipelines_token = os.getenv('PIPELINES_BEARER_TOKEN', '0p3n-w3bu!')
if pipelines_token:
    pipelines_token = pipelines_token.strip()

PIPELINES_BEARER_TOKEN = pipelines_token
PIPELINES_DIR = os.getenv("PIPELINES_DIR", "./lamb_assistants")
 
API_KEY = pipelines_token
# Ollama Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:latest')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-mini')

# Openwebui Authentication
OWI_PATH = os.getenv('OWI_PATH')
OWI_BASE_URL = os.getenv('OWI_BASE_URL', 'http://localhost:8080')
CHROMA_PATH = os.path.join(OWI_PATH, "vector_db") 

# Database Configuration
LAMB_DB_PATH = os.getenv('LAMB_DB_PATH')
LAMB_DB_PREFIX = os.getenv('LAMB_DB_PREFIX', '')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


# Signup Configuration
SIGNUP_ENABLED = os.getenv('SIGNUP_ENABLED', 'false').lower() == 'true'
SIGNUP_SECRET_KEY = os.getenv('SIGNUP_SECRET_KEY',"pepino-secret-key")

# OWI Admin Configuration
OWI_ADMIN_NAME = os.getenv('OWI_ADMIN_NAME', 'Admin')
OWI_ADMIN_EMAIL = os.getenv('OWI_ADMIN_EMAIL', 'admin@lamb.com')
OWI_ADMIN_PASSWORD = os.getenv('OWI_ADMIN_PASSWORD', 'admin')

# Validate required environment variables
required_vars = ['LAMB_DB_PATH', 'OWI_PATH']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
