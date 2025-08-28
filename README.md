# Northern University Timetable System

## Quick start
- Backend: see `backend/README.md`
- Frontend: see `frontend/README.md`
- Docker: `docker compose up --build`

## CI (suggested)
- Add a GitHub Actions workflow to run backend tests and frontend build on push/PR
# Northern University Project

A full-stack web application built with Django (backend), React (frontend), and MySQL (database).

## Project Structure

```
northernUNi/
├── backend/          # Django backend
├── frontend/         # React frontend
├── requirements.txt  # Python dependencies
├── package.json      # Node.js dependencies
├── env.example      # Environment variables template
└── README.md        # This file
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Git

## Setup Instructions

### 1. Python Virtual Environment

```bash
# Create virtual environment
python -m venv northernUNi

# Activate virtual environment
# On Windows:
northernUNi\Scripts\activate

# On macOS/Linux:
source northernUNi/bin/activate
```

### 2. Install Python Dependencies

```bash
# Make sure virtual environment is activated
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies

```bash
npm install
```

### 4. MySQL Database Setup

1. Install MySQL if not already installed
2. Create a new database:
   ```sql
   CREATE DATABASE northern_uni_db;
   CREATE USER 'your_username'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON northern_uni_db.* TO 'your_username'@'localhost';
   FLUSH PRIVILEGES;
   ```

### 5. Environment Configuration

1. Copy `env.example` to `.env`
2. Update the values with your actual database credentials

### 6. Django Setup

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 7. React Development Server

```bash
# In a new terminal
npm run dev
```

## Development

- Django backend runs on: http://localhost:8000
- React frontend runs on: http://localhost:3000
- Django admin: http://localhost:8000/admin

## Available Scripts

### Backend (Django)
- `python manage.py runserver` - Start development server
- `python manage.py makemigrations` - Create database migrations
- `python manage.py migrate` - Apply database migrations
- `python manage.py collectstatic` - Collect static files

### Frontend (React)
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues

## Database Models

The project includes basic models for:
- Users (Students, Faculty, Staff)
- Courses
- Departments
- Enrollments
- Grades

## API Endpoints

- `/api/auth/` - Authentication endpoints
- `/api/users/` - User management
- `/api/courses/` - Course management
- `/api/departments/` - Department management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
