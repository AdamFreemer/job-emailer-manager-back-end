# Job Tracker API - Backend

A Django-based backend for an AI-powered job application tracker that integrates with Gmail to automatically manage job applications, generate email drafts, and track application status.

## Features

- 🔐 Google OAuth integration for Gmail access
- 📧 Automatic email classification (job opportunities, responses, link lists)
- 🤖 AI-powered draft generation using OpenAI
- 🔗 Web crawling for job listings discovery
- 📊 Application status tracking (Applied, Interview, Offer, Rejected)
- 📅 Daily digest emails
- 🔄 Real-time Gmail synchronization via Celery

## Tech Stack

- **Framework**: Django 5.0.1 + Django REST Framework
- **Database**: PostgreSQL 15
- **Task Queue**: Celery 5.3 + Redis
- **AI**: OpenAI GPT-4
- **Web Scraping**: Playwright + BeautifulSoup4
- **Authentication**: Google OAuth 2.0
- **Deployment**: Docker + Gunicorn

## Prerequisites

- Python 3.12+
- PostgreSQL 15
- Redis
- Node.js (for Playwright)

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-emailer-back-end
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**
   ```bash
   createdb job_tracker_db
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Start Celery workers (in separate terminals)**
   ```bash
   # Worker for IO tasks
   celery -A job_tracker worker -Q io -l info
   
   # Worker for AI tasks
   celery -A job_tracker worker -Q ai -l info
   
   # Beat scheduler
   celery -A job_tracker beat -l info
   ```

## API Endpoints

### Health & Status
- `GET /` - API root information
- `GET /api/health/` - Basic health check
- `GET /api/health/detailed/` - Detailed health check with component status
- `GET /api/status/` - API version and feature flags

### Authentication (Coming Soon)
- `POST /api/oauth/google/` - Initiate Google OAuth
- `GET /api/oauth/google/callback/` - OAuth callback

### Applications (Coming Soon)
- `GET /api/apps/` - List applications
- `POST /api/apps/` - Create application
- `GET /api/apps/{id}/` - Get application details
- `PATCH /api/apps/{id}/` - Update application status

## Environment Variables

Create a `.env` file with the following variables:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=job_tracker_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Encryption
FIELD_ENCRYPTION_KEY=generate-a-key

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback

# OpenAI
OPENAI_API_KEY=your-api-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-app-password
```

## Testing

Run tests with:
```bash
pytest
```

For smoke tests:
```bash
python manage.py test core.tests.test_smoke
```

## Deployment

### Using Docker

```bash
docker-compose up -d
```

### Manual Deployment

1. Set `DEBUG=False` in production
2. Configure proper database credentials
3. Set up SSL/TLS
4. Use a production WSGI server (Gunicorn)
5. Set up reverse proxy (Nginx)

## Database Schema

See [entity_relationship_diagram.md](../entity_relationship_diagram.md) for the complete database schema.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[To be determined]