# Google Maps Lead Enrichment System

## Project Overview
This tool is designed to enrich lead data derived from Google Maps. It allows users to upload CSV/Excel files containing company information, automatically scrapes additional details (like emails and CEO names) from company websites, and provides a dashboard to monitor progress and export the enriched data.

## Features
- **Data Import**: Supports CSV and Excel (.xlsx, .xls) uploads.
- **Automated Enrichment**: Background scraping of company websites to find:
  - Emails
  - Physical Addresses
  - CEO/Owner Name (placeholder logic)
- **Dashboard**: Real-time progress monitoring of processed leads.
- **Export**: Download fully enriched data as CSV.
- **Database**: Uses SQLite for lightweight, local data storage.

## Prerequisites
Before hosting or running this project, ensure you have the following installed:
- **Python 3.8+**
- **pip** (Python package installer)

## Installation

1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd lead_scraper
   ```

2. **Create a Virtual Environment**
   It is recommended to use a virtual environment to manage dependencies.
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
The application uses default configurations suitable for local development.
- **Database**: A `leads.db` SQLite file will be automatically created in the root directory.
- **Port**: The application defaults to running on port `8000`.

## Running the Application

To start the server, run the following command from the project root:

```bash
uvicorn app.main:app --reload
```
*The `--reload` flag enables auto-reload on code changes, useful for development.*

For production use (without auto-reload):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Once running, access the dashboard at:
**http://localhost:8000/dashboard**

## Project Structure

```
├── app/
│   ├── main.py          # Application entry point & API routes
│   ├── database.py      # Database connection & session handling
│   ├── models.py        # SQLAlchemy database models
│   ├── scraper.py       # Web scraping logic
│   ├── processor.py     # Background task processing logic
│   └── validator.py     # Data validation utilities
├── frontend/
│   └── index.html       # Dashboard UI
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Usage Guide

### 1. Upload Leads
- Navigate to the dashboard.
- Click "Choose File" and select your CSV or Excel file.
- **Required Columns**: The system looks for flexible column names such as:
  - `Company Name`, `Name`, `Company`
  - `Website`, `URL`
  - `Phone`, `Phone Number`
  - `Rating`
  - `Source`

### 2. Monitoring
- The dashboard updates in real-time.
- **Total**: Total rows uploaded.
- **Pending**: Waiting to be processed.
- **Processing**: Currently being scraped.
- **Done**: Successfully enriched.

### 3. Export Data
- Click the "Export CSV" button to download the `final_leads.csv` file containing all original data plus enriched fields.

## Troubleshooting

- **Database Errors**: If you encounter issues, try deleting `leads.db` and restarting the application to regenerate the schema.
- **Scraping Blockages**: Repeated requests to the same site may be blocked. Ensure fair usage.

## License
[Your License Here]
