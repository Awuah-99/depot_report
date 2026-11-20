# Depot Order Status Report Generator

A lightweight, automated Python tool designed for Bulk Oil Distribution Companies and Oil Marketing Companies. It fetches daily depot loading activities from the Persol Systems API, categorizes orders by their current status, and generates a comprehensive, formatted PDF report.

## Features
- **Zero-Database Architecture**: Processes data entirely in-memory using optimized Pandas vectorization. No PostgreSQL or SQLite setup required.
- **Automated PDF Generation**: Creates a multi-page, landscape PDF with an executive summary, PMS/AGO pie chart, and detailed tables for every order status.
- **Status Tracking**: Automatically splits the messy multi-section Excel export into a unified dataset tagged with order statuses (e.g., `Approved`, `Loaded`, `BDC Decline`).
- **Resilient Fetching**: Built-in async retries and timeout handling for API requests.

## Pipeline Architecture
1. **Fetch**: Asynchronously downloads the daily Excel report from the depot API.
2. **Process**: Parses the Excel file, identifies section boundaries, standardizes columns, and filters by your configured depot.
3. **Report**: Generates a Matplotlib-based PDF with summary charts and paginated data tables.

## Installation

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

### LICENCE
Distributed under the MIT License.

