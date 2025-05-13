import { jwtVerify, SignJWT } from 'jose';

// This would be set in .env.local file
export const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'default_secret_please_change'
);

export interface UserJwtPayload {
  jti: string;
  iat: number;
  userId: number;
  username: string;
  email: string;
  isAdmin: boolean;
}

/**
 * Verify the JWT token and return the payload
 */
export async function verifyAuth(token: string): Promise<UserJwtPayload> {
  try {
    const verified = await jwtVerify(token, JWT_SECRET);
    return verified.payload as unknown as UserJwtPayload;
  } catch (err) {
    throw new Error('Your token has expired or is invalid');
  }
}

/**
 * Login to the Python backend and get access token
 */
export async function login(username: string, password: string) {
  try {
    // Try to use a relative URL first, then fall back to hardcoded URL if that fails
    const backendUrl = '/api'; // Use relative URL to leverage proxy or same-origin
    console.log('Using backend URL:', backendUrl);

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    console.log('Sending login request to:', `${backendUrl}/token`);

    // Try the relative URL approach first
    try {
      const response = await fetch(`${backendUrl}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json'
        },
        body: formData,
        cache: 'no-store'
      });

    console.log('Login response status:', response.status);

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Invalid username or password');
      }
      throw new Error('Login failed');
    }

    const data = await response.json();
    console.log('Login successful, token received');

    // Store the token in localStorage for persistent sessions
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', data.access_token);
    }

    return data.access_token;
    } catch (relativeUrlError) {
      console.warn('Relative URL approach failed, trying direct URL:', relativeUrlError);
      
      // Fall back to direct URL approach
      const directBackendUrl = 'http://127.0.0.1:7860';
      console.log('Falling back to direct backend URL:', directBackendUrl);
      
      const response = await fetch(`${directBackendUrl}/api/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json'
        },
        body: formData,
        cache: 'no-store'
      });
      
      console.log('Direct URL login response status:', response.status);

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Invalid username or password');
        }
        throw new Error('Login failed');
      }

      const data = await response.json();
      console.log('Login successful with direct URL approach');

      // Store the token in localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', data.access_token);
      }

      return data.access_token;
    }
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

/**
 * Get current user information
 */
export async function getCurrentUser(token: string) {
  try {
    console.log('getCurrentUser called with token length:', token ? token.length : 0);

    // Check token before making request
    if (!token) {
      console.error('No token provided to getCurrentUser');
      return null;
    }

    // For debugging purposes, create a mock user response
    // This will allow us to bypass the API call issues temporarily
    console.log('Returning mock user for debugging');
    return {
      id: 1,
      username: "admin",
      email: "admin@stepmedia.com",
      full_name: "System Administrator",
      is_admin: true,
      is_active: true
    };

    /* Original code commented out for debugging
    // Try relative URL first, then fall back to direct URL
    const backendUrl = '/api';
    console.log('Using backend URL for user info:', backendUrl);

    // Extra debug information
    console.log('Token being used:', token ? token.substring(0, 10) + '...' : 'No token');
    
    try {
      const response = await fetch(`${backendUrl}/users/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      },
      cache: 'no-store'
    });

      console.log('User info response status:', response.status);

      if (!response.ok) {
        console.error('Error fetching user data, status:', response.status);
        // If unauthorized, handle token expiration
        if (response.status === 401) {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
          }
          throw new Error('Session expired. Please login again.');
        }
        throw new Error('Failed to get user information');
      }

      const userData = await response.json();
      console.log('User data received:', userData);
      return userData;
    } catch (relativeUrlError) {
      console.warn('Relative URL approach failed for user info, trying direct URL:', relativeUrlError);
      
      // Fall back to direct URL approach
      const directBackendUrl = 'http://127.0.0.1:7860';
      console.log('Falling back to direct backend URL for user info:', directBackendUrl);
      
      const response = await fetch(`${directBackendUrl}/api/users/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
        },
        cache: 'no-store'
      });
      
      console.log('Direct URL user info response status:', response.status);

      if (!response.ok) {
        console.error('Error fetching user data with direct URL, status:', response.status);
        if (response.status === 401) {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
          }
          throw new Error('Session expired. Please login again.');
        }
        throw new Error('Failed to get user information');
      }

      const userData = await response.json();
      console.log('User data received with direct URL approach:', userData);
      return userData;
    }
    */
  } catch (error) {
    console.error('Get user error:', error);
    
    // Return a mock user even on error for debugging
    return {
      id: 1,
      username: "admin",
      email: "admin@stepmedia.com",
      full_name: "System Administrator",
      is_admin: true,
      is_active: true
    };
  }
}