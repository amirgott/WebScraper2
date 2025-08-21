# Events Data Aggregator for "17 SDGs" Portal

This application aggregates event data from various sources (text, URLs, images, PDFs) to populate a database of events related to the UN's 17 Sustainable Development Goals (SDGs).

## Features

- Extracts event information from multiple media sources
- Processes free-format text with embedded URLs
- OCR for images to extract event details
- PDF text extraction
- Hard-limited URL scraping (depth 0 and 1 only)
- Validation and aggregation of information
- Export to Google Sheets
- LLM-powered information extraction using Google's Gemini model

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API Key
- Google Service Account with access to Google Sheets
- Google Sheets document ID (with write permissions for user account)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API keys and configuration

### Environment Variables

Create a `.env` file with the following variables:

```
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Google Sheets
GOOGLE_SHEET_ID=your_google_sheet_id_here

# Path to service account credentials JSON file
SERVICE_ACCOUNT_FILE=path_to_your_service_account_file.json
```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Use the web interface to input:
   - Free-format text (with or without URLs)
   - Images (drag & drop, paste from clipboard, or file upload)
   - PDF files

4. Click "Run" to start the aggregation process

5. The extracted event information will be displayed and added to the configured Google Sheet

## Project Structure

- `app.py` - Main Flask application
- `src/` - Source code
  - `utils/` - Utility functions
  - `scrapers/` - Scraping modules
  - `workflows/` - Processing workflows
- `config/` - Configuration files
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JavaScript)

## Deployment

The application can be deployed using Docker:

```
docker build -t events-data-aggregator .
docker run -p 5000:5000 events-data-aggregator
```

Alternatively, it can be deployed to cloud platforms such as Render.com.

## License

This project is proprietary and confidential.
