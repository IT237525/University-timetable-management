# Backend Deployment & Testing

## Local dev
- Activate the provided venv `northernUNi` or your own
- Run: `python manage.py migrate && python manage.py runserver`

## Docker
```
docker compose up --build
```
- Backend at http://localhost:8000
- Frontend at http://localhost:3000

## Tests
```
python manage.py test api
```

## Production notes
- Set `DEBUG=0`, configure `ALLOWED_HOSTS`
- Configure `EMAIL_BACKEND` and `DEFAULT_FROM_EMAIL`
- Add a real DB (PostgreSQL/MySQL) and update `DATABASES`
- Serve static files via CDN or reverse proxy

