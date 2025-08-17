# import easyocr
import requests
import tempfile
from PIL import Image
import os

class ImageProcessor:
    def __init__(self):
        """Initialize the image processor with OCR"""
        # Initialize EasyOCR with Hebrew and English languages
        self.reader = None  # Lazy loading to save resources

    def _initialize_reader(self):
        """Lazy initialization of EasyOCR reader"""
        if self.reader is None:
            self.reader = easyocr.Reader(['he', 'en'])

    def process_image_url(self, image_url):
        """Process an image from a URL"""
        try:
            # Download the image
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Process the image file
            result = self.process_image_file(temp_file_path)

            # Clean up the temporary file
            os.unlink(temp_file_path)

            return result

        except Exception as e:
            print(f"Error processing image URL {image_url}: {str(e)}")
            return ""

    def process_image_file(self, image_path):
        """Process an image file using OCR"""
        try:
            # Ensure the image exists
            if not os.path.exists(image_path):
                print(f"Image file not found: {image_path}")
                return ""

            # Open and preprocess the image
            image = Image.open(image_path)

            # Initialize the OCR reader
            self._initialize_reader()

            # Run OCR
            result = self.reader.readtext(image_path)

            # Extract and concatenate the text
            text = ' '.join([detection[1] for detection in result])

            return text

        except Exception as e:
            print(f"Error processing image file {image_path}: {str(e)}")
            return ""
