import google.generativeai as genai
from src.utils.config import get_gemini_api_key

class LLMClient:
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
            return response.text
        except Exception as e:
            print(f"Error in LLM processing: {str(e)}")
            return None

    def extract_event_info(self, text, schema):
        """Extract event information from text using LLM"""
        # Build prompt for extracting event info
        prompt = self._build_event_extraction_prompt(text, schema)
        response = self.process_data(
            prompt,
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

    def _build_event_extraction_prompt(self, text, schema):
        """Build prompt for extracting event information"""
        schema_description = "\n".join([f"{field}: {info['description']}" for field, info in schema.items()])

        prompt = f"""
        Extract information about an event from the following text. The information should be structured according to these fields:

        {schema_description}

        Format your response as a JSON object with the field names as keys. If information for a field is not available, 
        use an empty string for that field. For the 'תעשיה' field, select from the 17 UN SDGs based on the content.

        TEXT:
        {text}
        """
        return prompt
