# StepmediaHRM - HR Management System with Facial Recognition

An HR Management System built with Next.js and Python that includes facial recognition capabilities and SQLite database integration.

## Architecture

This application consists of three main components:

1. **Next.js Frontend**: A modern web application providing the UI for the HR management system
2. **Python Backend**: Provides facial recognition capabilities and other AI-powered features using Gradio and FastAPI
3. **SQLite Database**: Local database for storing user accounts, employee data, and facial recognition data

## Features

- Employee management
- Attendance tracking
- Leave management
- Facial recognition for employee verification
- Role-based access control
- Reporting and analytics

## Getting Started

The application is configured to run with Pinokio, which handles setting up and running both the frontend and backend.

### To run the application:

1. Install the app in Pinokio
2. Click "Start" from the Pinokio interface
3. Access the web UI through the "Open Web UI" button

### Default Login Credentials

```
Username: admin
Password: admin123
```

**Important**: Please change the default password after first login for security.

## Development

The Python backend is located in `app.py` at the root of the app directory.
The Next.js frontend is in the `src` directory, with pages in `src/app`.
The SQLite database schema is defined in `db/models.py`.

### Database Structure

The application uses SQLite with the following main tables:
- `users`: User accounts for system access
- `employees`: Employee records
- `attendance`: Employee attendance records
- `leave_requests`: Leave requests submitted by employees
- `facial_data`: Facial recognition data for employees
- `roles`: User roles for access control

### Facial Recognition Testing

You can test the Python backend integration in the Facial Recognition page.
- Use the "Test Python Backend" button to check the connection
- Use the "Open Gradio Interface" button to access the dedicated facial recognition interface

### Setup for local development:

```bash
# Install dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Start both frontend and backend
npm run dev

# In a separate terminal, start the Python backend
python app.py
```

### Working with the database:

The system automatically initializes the database with default data including an admin user. You can interact with the database through the FastAPI endpoints or directly using SQLAlchemy in the Python backend.
