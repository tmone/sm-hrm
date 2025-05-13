import { API_URL } from './constants';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface UserSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  leave_alerts: boolean;
}

export interface UpdateProfileRequest {
  username?: string;
  email?: string;
  full_name?: string;
  password?: string;
}

export interface UpdateSettingsRequest {
  email_notifications?: boolean;
  push_notifications?: boolean;
  leave_alerts?: boolean;
}

// Get current user profile
export async function fetchUserProfile(): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/api/users/me`);
  
  if (!response.ok) {
    throw new Error(`Error fetching user profile: ${response.status}`);
  }
  
  return await response.json();
}

// Update user profile
export async function updateUserProfile(profileData: UpdateProfileRequest): Promise<UserProfile> {
  // If password is provided, separate it as it requires a different endpoint
  const { password, ...profileFields } = profileData;
  
  let profile;
  
  // Update profile fields
  if (Object.keys(profileFields).length > 0) {
    const profileResponse = await fetch(`${API_URL}/api/users/me/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileFields),
    });
    
    if (!profileResponse.ok) {
      throw new Error(`Error updating user profile: ${profileResponse.status}`);
    }
    
    profile = await profileResponse.json();
  } else {
    // If only updating password, still need to fetch current profile
    profile = await fetchUserProfile();
  }
  
  // Update password if provided
  if (password) {
    const passwordResponse = await fetch(`${API_URL}/api/users/me/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ new_password: password }),
    });
    
    if (!passwordResponse.ok) {
      throw new Error(`Error updating password: ${passwordResponse.status}`);
    }
  }
  
  return profile;
}

// Get user settings
export async function fetchUserSettings(): Promise<UserSettings> {
  const response = await fetch(`${API_URL}/api/users/me/settings`);
  
  if (!response.ok) {
    // Return default settings if endpoint not implemented yet
    if (response.status === 404) {
      return {
        email_notifications: true,
        push_notifications: false,
        leave_alerts: true
      };
    }
    throw new Error(`Error fetching user settings: ${response.status}`);
  }
  
  return await response.json();
}

// Update user settings
export async function updateUserSettings(settingsData: UpdateSettingsRequest): Promise<UserSettings> {
  const response = await fetch(`${API_URL}/api/users/me/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settingsData),
  });
  
  if (!response.ok) {
    throw new Error(`Error updating user settings: ${response.status}`);
  }
  
  return await response.json();
}