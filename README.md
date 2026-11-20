# Depot Order Status Report Generator

A lightweight, automated Python tool designed for Bulk Oil Distribution Companies and Oil Marketing Companies. It fetches daily depot loading activities from the Persol Systems API, categorizes orders by their current status, and generates a comprehensive, formatted PDF report.

### Prerequisites
- Python 3.8+
- Git

### Setup
```bash
git clone https://github.com/Awuah-99/depot_report.git
cd depot_report
# Create and activate a virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
#Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory to store your API credentials and depot configuration.

```bash
touch .env
```

### Usage
# Run the full pipeline (Fetch -> Process -> Generate PDF)
python main.py

### LICENSE
Distributed under the MIT License.

