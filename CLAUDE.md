# Context for Claude

## User Background
- Has experience with Ruby on Rails framework
- When explaining Django/Python concepts, relate them to Rails/Ruby equivalents when possible
- Familiar with RESTful conventions from Rails (resources, controllers, etc.)

## Project Context
This is a job application tracker that integrates with Gmail to:
- Fetch and classify job-related emails
- Generate AI-powered email drafts
- Track application status through a pipeline
- Extract and analyze job listings from emails

## Technical Stack
- Backend: Django + Django REST Framework (similar to Rails + Rails API)
- Task Queue: Celery (similar to Sidekiq in Rails)
- Database: PostgreSQL
- Frontend: React + Mantine UI
- Deployment: Heroku backend, Vercel frontend

## Key Comparisons for Explanations
- Django ViewSets ≈ Rails Controllers
- Django Models ≈ Rails Models (Active Record)
- Django REST Framework Router ≈ Rails resources routes
- Celery ≈ Sidekiq
- Django migrations ≈ Rails migrations
- pip/requirements.txt ≈ bundler/Gemfile

## Development Preferences
- Explain Django concepts by comparing to Rails equivalents
- Use Rails terminology as reference points
- Show side-by-side comparisons when helpful