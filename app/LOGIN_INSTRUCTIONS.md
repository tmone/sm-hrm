# Login Instructions for StepmediaHRM

The application now has a SQLite database with a default admin user, allowing you to log in and access all features.

## Login Credentials

To log in to the StepmediaHRM application:

- **Username:** admin
- **Password:** admin123

## Troubleshooting Login Issues

If you encounter login issues, here are some steps to resolve them:

1. **Ensure both servers are running:**
   - The Python backend server should be running on port 7860
   - The Next.js frontend should be running on port 3000 or 9002

2. **Check the console for errors:**
   - Open browser developer tools (F12 or right-click → Inspect)
   - Look for any errors in the Console tab

3. **Restart the application:**
   ```bash
   # Stop any running instances
   pkill -f "python app.py"
   
   # Start the application again in Pinokio
   ```

4. **Manual database initialization:**
   If needed, you can manually initialize the database with:
   ```bash
   cd /home/tmone/pinokio/api/StepmediaHRM/app
   python -c "from db.init_db import init_db; init_db()"
   ```

5. **Test the API endpoints:**
   ```bash
   # Test authentication endpoint
   curl -X POST -d 'username=admin&password=admin123' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     http://127.0.0.1:7860/api/token
   
   # The response should contain an access_token
   ```

## Security Note

After your first login, it's recommended to change the default password for security reasons. This feature will be available in the user settings.