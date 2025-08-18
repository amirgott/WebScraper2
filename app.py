import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import base64
import tempfile
from werkzeug.utils import secure_filename

from src.workflows.orchestrator import WorkflowOrchestrator
from src.utils.config import load_event_schema

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Load event schema
event_schema = load_event_schema()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api-check')
def api_check():
    """A simple endpoint to check if the API is accessible"""
    return jsonify({
        'status': 'ok',
        'message': 'API is accessible',
        'endpoints': {
            'run_scrape': '/run_scrape (POST)'
        }
    })

@app.route('/run_scrape', methods=['POST'])
def run_scrape():
    """Endpoint to run the scraping process"""
    try:
        # Get input data from request
        app.logger.info(f"Form data received: {request.form.keys()}")
        free_format_text = request.form.get('free_format_text', '')
        app.logger.info(f"Free format text: {free_format_text[:100] if free_format_text else 'None'}")  # Log first 100 chars

        # Initialize orchestrator and run workflows
        orchestrator = WorkflowOrchestrator(event_schema)
        result = orchestrator.run(free_format_text)

        return jsonify({
            'success': True,
            'message': 'Scraping completed successfully',
            'result': result
        })

    except Exception as e:
        app.logger.error(f"Error in run_scrape: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
