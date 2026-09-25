# AI Resume Screener

A lightweight web application and REST API that ranks multiple resumes against a job description using semantic similarity.

## Features
- Upload multiple PDF and DOCX files.
- Rank resumes based on cosine similarity to the job description using `all-MiniLM-L6-v2`.
- Handles file extraction, chunking, and mean-pooling of semantic embeddings.
- Simple Web UI and REST API endpoint (`POST /rank`).

## Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone or download this project.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
The application will be available at:
- Web UI: http://localhost:8000/
- API Documentation (Swagger UI): http://localhost:8000/docs

## Testing

Run the automated tests using pytest:
```bash
pytest tests/
```
