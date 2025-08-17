from src.scrapers.image_processor import ImageProcessor
from src.utils.llm_client import LLMClient

class ImageWorkflow:
    def __init__(self, event_schema):
        """Initialize the image workflow"""
        self.event_schema = event_schema
        self.image_processor = ImageProcessor()
        self.llm_client = LLMClient()

    def process(self, image_data):
        """Process an image (URL or file)"""
        # Skip empty image data
        if not image_data:
            return {}, []

        # Extract text from image
        if isinstance(image_data, str):  # Image URL
            ocr_text = self.image_processor.process_image_url(image_data)
        elif isinstance(image_data, dict) and image_data.get('type') == 'file':  # Image file
            ocr_text = self.image_processor.process_image_file(image_data.get('path', ''))
        else:
            return {}, []

        # Skip if no text was extracted
        if not ocr_text:
            return {}, []

        # Log the size of extracted text
        image_id = image_data if isinstance(image_data, str) else image_data.get('path', 'image file')
        print(f"Image {image_id}: Extracted {len(ocr_text)} characters of text")

        # Extract event information from text
        event_record = self.llm_client.extract_event_info(ocr_text, self.event_schema)

        # Add image URL to event record if any information was found
        if event_record and any(event_record.values()):
            if isinstance(image_data, str):  # Image URL
                if 'IMAGE' in event_record:
                    if image_data not in event_record['IMAGE']:
                        if event_record['IMAGE']:
                            event_record['IMAGE'] += f", {image_data}"
                        else:
                            event_record['IMAGE'] = image_data
                else:
                    event_record['IMAGE'] = image_data

        # Find URLs in the OCR text
        urls = self.llm_client.find_urls_in_text(ocr_text)

        # Prepare new sources to process
        new_sources = [('url', url) for url in urls]

        # Log the sources that will be returned for further processing
        image_id = image_data if isinstance(image_data, str) else image_data.get('path', 'image file')
        print(f"Image {image_id}: Returning {len(urls)} URLs found in OCR text for further processing")
        if urls:
            print(f"  URLs from image: {', '.join(urls)}")

        return event_record, new_sources
