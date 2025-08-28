FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY northernUNi /venv
ENV VIRTUAL_ENV=/venv \
    PATH="/venv/Scripts:/venv/bin:$PATH"

COPY backend /app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


