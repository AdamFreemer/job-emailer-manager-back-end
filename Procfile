web: gunicorn job_tracker.wsgi --log-file -
worker: celery -A job_tracker worker -Q io,ai -l info
beat: celery -A job_tracker beat -l info