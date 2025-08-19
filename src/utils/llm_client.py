from abc import ABC, abstractmethod
from datetime import date

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: 'google.generativeai' not found. GenaiLLMClient will not be usable.")
    genai = None

try:
    import openai
except ImportError:
    print("Warning: 'openai' not found. OpenAiLLMClient will not be usable.")
    openai = None

from src.utils.config import get_gemini_api_key, get_openai_api_key

class LLMClient(ABC):
    @abstractmethod
    def __init__(self):
        """Initialize the LLM client into self.model """
        pass

    @abstractmethod
    def process_data(self, prompt, temperature=0.0, generation_config_override=None
):
        """Process data with the LLM model
        return the response text or None if an error occurred"""
        pass

    def extract_event_info(self, text, schema, existing_event_record=None):
        """Extract event information from text using LLM"""
        # Build prompt for extracting event info
        prompt = self._build_event_extraction_prompt(text, schema, existing_event_record)
        response = self.process_data(prompt,
            generation_config_override={"response_mime_type": "application/json"}
        )

        if not response:
            return {}

        # Parse the response into a structured event record
        try:
            import json
            return json.loads(response)
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            print(f"Raw response: {response}")
            return {}


    def find_urls_in_text(self, text):
        """Find URLs in text that seem to lead to event-related pages"""
        prompt = f"""
        Extract all URLs from the following text that seem to lead to event-related pages 
        (like registration pages, event details, etc.).
        Return only the URLs, one per line, without any additional text.
        If no URLs are found, respond with 'No URLs found'.

        Text:
        {text}
        """
        response = self.process_data(prompt)
        if response and 'No URLs found' not in response:
            return [url.strip() for url in response.strip().split('\n') if url.strip().startswith('http')]
        return []

    def find_event_related_urls(self, url_list):
        """Find URLs from a list that seem to be related to events"""
        if not url_list:
            return []

        prompt = f"""
        From the following list of tags that include URLs, identify those that are likely related to events 
        (conferences, webinars, workshops, etc.).
        Return only the URLs, one per line, without any additional text.
        If no URLs seem event-related, respond with 'No event URLs found'.

        URLs:
        {chr(10).join(url_list)}
        """
        response = self.process_data(prompt)
        if response and 'No event URLs found' not in response:
            return [url.strip() for url in response.strip().split('\n') if url.strip().startswith('http')]
        return []

    def find_event_related_images(self, image_urls):
        """Find image URLs that seem to be related to events"""
        if not image_urls:
            return []

        prompt = f"""
        From the following list of image URLs, identify those that are likely related to events 
        (conferences, webinars, workshops, etc.). Consider image URLs that contain words like 'event', 'conference', 
        'invitation', 'banner', etc.
        Return only the URLs, one per line, without any additional text.
        If no images seem event-related, respond with 'No event images found'.

        Image URLs:
        {chr(10).join(image_urls)}
        """
        response = self.process_data(prompt)
        if response and 'No event images found' not in response:
            return [url.strip() for url in response.strip().split('\n') if url.strip().startswith('http')]
        return []

    def _build_event_extraction_prompt(self, text, schema, existing_event_record=None):
        """Build prompt for extracting event information"""
        schema_description = "\n".join([f"{field}: {info['description']}" for field, info in schema.items()])

        # Build existing event context if provided
        existing_context = ""
        if existing_event_record:
            # Filter out empty fields for context
            non_empty_fields = {k: v for k, v in existing_event_record.items() if v and str(v).strip()}
            if non_empty_fields:
                existing_values = "\n".join([f"{field}: {value}" for field, value in non_empty_fields.items()])
                existing_context = f"""
        
        EXISTING EVENT INFORMATION:
        We already have partial information about an event. Only extract information from the text if it relates to the SAME event as described below. If the text appears to describe a different event or contains too many contradictions to the existing information, return an empty JSON object {{}}.
        
        Current event details:
        {existing_values}
        
        INSTRUCTION: Assess whether the new text relates to the same event. If it does, extract only additional or consistent information. If it describes a different event or has major contradictions, return empty fields."""

        prompt = f"""
        Extract information about an event from the following text. The information should be structured according to these fields:

        {schema_description}{existing_context}

        Format your response as a JSON object with the field names as keys. If information for a field is not available, 
        use an empty string for that field. For the 'תעשיה' field, select from the 17 UN SDGs based on the content.
        For the 'לינק להרשמה' field, check the below text for a section that include such a link and extract the URL 
        or if there's a form for registration put in the URL the text was extracted from.
        Never estimate values. Specifically for 'משעה' and 'עד שעה', assign values only if they explicitly appear in the text.
        Note the current date and time when extracting the information: {date.today()}. If no year is specified, assume the current year.

        TEXT:
        {text}
        """
        return prompt


class GenaiLLMClient(LLMClient):

    def __init__(self):
        """Initialize the LLM client with Gemini model"""
        api_key = get_gemini_api_key()
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def process_data(self, prompt, temperature=0.0, generation_config_override=None
                     ):
        """Process data with the LLM model"""
        try:
            config_dict = {
                "temperature": temperature,
                "max_output_tokens": 8192,
            }
            if generation_config_override:
                config_dict.update(generation_config_override)

            generation_config = genai.GenerationConfig(**config_dict)

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            print(response)
            return response.text
        except Exception as e:
            print(f"Error in LLM processing: {str(e)}")
            return None


class OpenAiLLMClient(LLMClient):

    def __init__(self, model="gpt-4o"):
        """Initialize the LLM client with an OpenAI model"""
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # The 'model' attribute is named for consistency with the abstract class,
        # but it holds the client instance.
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model

    def process_data(self, prompt, temperature=0.0, generation_config_override=None):
        """Process data with the OpenAI model"""
        try:
            # Prepare parameters for the OpenAI API call
            params = {
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": 4096,  # A sensible default, adjust as needed
                "messages": [{"role": "user", "content": prompt}]
            }

            # Translate generation_config_override to OpenAI-specific parameters
            if generation_config_override:
                if generation_config_override.get("response_mime_type") == "application/json":
                    params["response_format"] = {"type": "json_object"}

            # Make the API call
            response = self.client.chat.completions.create(**params)

            # Extract and return the response text
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error in OpenAI LLM processing: {str(e)}")
            return None

# --- Factory Implementation ---

# Module-level dictionary to cache client instances
_llm_clients = {}

def get_llm_client(client_name: str) -> LLMClient:
    """
    Factory function to get an LLM client instance.

    This function uses a cache to ensure that only one instance of each
    client type is created during the application's lifecycle.

    Args:
        client_name (str): The name of the client to retrieve ('OpenAi' or 'Genai').

    Returns:
        LLMClient: An instance of the requested LLM client.

    Raises:
        ValueError: If the client_name is not supported.
    """
    # Normalize the name to handle different casings (e.g., 'openai', 'OpenAI')
    normalized_name = client_name.lower()

    # If the client already exists in our cache, return it
    if normalized_name in _llm_clients:
        print(f"Returning cached '{client_name}' client.")
        return _llm_clients[normalized_name]

    # If not cached, create a new instance
    print(f"Creating new '{client_name}' client.")
    if normalized_name == 'openai':
        client = OpenAiLLMClient()
        _llm_clients[normalized_name] = client
        return client
    elif normalized_name == 'genai':
        client = GenaiLLMClient()
        _llm_clients[normalized_name] = client
        return client
    else:
        raise ValueError(f"Unsupported LLM client: '{client_name}'. Please use 'OpenAi' or 'Genai'.")
