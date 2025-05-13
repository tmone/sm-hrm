# StepmediaHRM Authentication System

The StepmediaHRM application now includes a complete authentication system using SQLite, SQLAlchemy, JWT tokens, and secure password hashing. This document explains how to use and extend this authentication system.

## Authentication Flow

1. **Login**: Users provide credentials (username/password) at the login page
2. **API Authentication**: The credentials are sent to the Python backend via the `/api/token` endpoint
3. **Token Generation**: Upon valid authentication, the backend returns a JWT token
4. **Store Token**: The token is stored in localStorage in the browser
5. **Session Management**: The token is included in subsequent API requests via Authorization header
6. **User Information**: User data is fetched from the `/api/users/me` endpoint

## Database Structure

The authentication system uses these main tables:

1. **users**: Stores user accounts with hashed passwords
2. **roles**: Defines user roles for access control
3. **user_roles**: Many-to-many relationship between users and roles

## Default Account

The system comes with a default admin account:
- **Username**: `admin`
- **Password**: `admin123`

**Important**: Change this password after the first login for security.

## Adding New Users

New users can be added in two ways:

1. **Through the API**: Using the `/api/users` endpoint (admin only)
2. **Programmatically**: By modifying the `init_db.py` script

Example API call to create a user:
```
POST /api/users
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "username": "newuser",
  "email": "newuser@example.com",
  "full_name": "New User",
  "password": "securepassword"
}
```

## Role-Based Access Control

The system includes predefined roles:
- **admin**: Full access to all features
- **hr**: Access to employee management
- **manager**: Team management capabilities
- **employee**: Limited access for regular employees

## Extending the Authentication System

To add new features to the authentication system:

1. **New User Fields**: Add fields to the `User` model in `db/models.py`
2. **Custom Roles**: Add new roles in `db/init_db.py`
3. **Password Policy**: Modify `db/auth.py` to enforce stronger password requirements
4. **Token Expiration**: Adjust `ACCESS_TOKEN_EXPIRE_MINUTES` in `db/auth.py`

## Troubleshooting

Common issues and solutions:

1. **Login Fails**: 
   - Ensure the Python backend is running
   - Check console for errors
   - Verify database connection

2. **Authentication Errors**:
   - Token might be expired (default is 30 minutes)
   - Backend might have restarted, requiring re-login
   - Check if the database file exists and is accessible

3. **Database Reset**:
   - To reset the database, delete the `hrm.db` file and restart the app
   - Run `python -c "from db.init_db import init_db; init_db()"` to re-initialize