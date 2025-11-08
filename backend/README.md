# FastAPI Backend - AI QA System

FastAPI backend for the AI-Powered Batch QA System MVP.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL (Neon)
- Google Cloud SDK
- Docker (optional)

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs (Swagger UI)

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routes/              # API routes
│   ├── services/            # Business logic
│   ├── middleware/          # Auth middleware
│   ├── utils/               # Utilities
│   ├── tasks/               # Background tasks
│   └── tests/               # Tests
├── migrations/              # Alembic migrations
├── requirements.txt         # Dependencies
├── Dockerfile              # Docker config
└── docker-compose.yml      # Local development
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Recordings
- `POST /api/recordings/signed-url` - Get signed upload URL
- `POST /api/recordings/upload` - Create recording
- `GET /api/recordings/list` - List recordings
- `GET /api/recordings/{id}` - Get recording

### Evaluations
- `GET /api/evaluations/{recording_id}` - Get evaluation
- `GET /api/evaluations/{id}/scores` - Get category scores
- `GET /api/evaluations/{id}/violations` - Get violations

### Policy Templates
- `POST /api/templates` - Create template
- `GET /api/templates` - List templates
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

## Deployment

### Docker
```bash
docker build -t ai-qa-backend .
docker run -p 8000:8080 ai-qa-backend
```

### Cloud Run
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/api:latest
gcloud run deploy api --image gcr.io/PROJECT_ID/api:latest
```

## Testing
```bash
pytest
```

## Environment Variables

See `.env.example` for all required environment variables.

