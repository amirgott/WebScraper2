import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env_variable(name, default=None):
    """Get environment variable or return default"""
    return os.environ.get(name, default)

def load_event_schema():
    """Load event schema from JSON file"""
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'event_schema.json')

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Add format information based on field descriptions
    for field, info in schema.items():
        # Default format is free text
        info['format'] = 'free_text'

        # Determine format based on description
        description = info.get('description', '').lower()

        if 'dd.mm.yy' in description:
            info['format'] = 'date'
        elif '24:00' in description:
            info['format'] = 'time'
        elif 'weekday' in description:
            info['format'] = 'day_of_week'
        elif 'לינק' in description or 'url' in description.lower():
            info['format'] = 'url'
        elif field in ['תעשיה', 'תעשיה 2']:
            info['format'] = 'sdg_list'
        elif field in ['אירועי פיזי/אונליין']:
            info['format'] = 'event_type'

    return schema

def get_gemini_api_key():
    """Get Google Gemini API key"""
    return get_env_variable('GEMINI_API_KEY')

def get_openai_api_key():
    """Retrieves the OpenAI API key from environment variables."""
    return get_env_variable("OPENAI_API_KEY")

def get_llm_client_name():
    """Get LLM client name"""
    return get_env_variable('LLM_CLIENT_NAME')

def get_google_sheet_id():
    """Get Google Sheet ID"""
    return get_env_variable('GOOGLE_SHEET_ID')

def get_service_account_json():
    """Get path to service account credentials file"""
    return get_env_variable('SERVICE_ACCOUNT_JSON')
