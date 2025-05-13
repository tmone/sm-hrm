import { API_URL } from './constants';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  roles: Role[];
  last_login?: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  full_name: string;
  password: string;
  is_admin?: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  full_name?: string;
  is_active?: boolean;
  is_admin?: boolean;
}

export interface UpdatePasswordRequest {
  new_password: string;
}

// Get all users
export async function fetchUsers(): Promise<User[]> {
  const response = await fetch(`${API_URL}/api/users`);
  
  if (!response.ok) {
    throw new Error(`Error fetching users: ${response.status}`);
  }
  
  return await response.json();
}

// Get a user by ID
export async function fetchUserById(userId: number): Promise<User> {
  const response = await fetch(`${API_URL}/api/users/${userId}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching user: ${response.status}`);
  }
  
  return await response.json();
}

// Search users
export async function searchUsers(searchTerm: string): Promise<User[]> {
  const response = await fetch(`${API_URL}/api/users/search?q=${encodeURIComponent(searchTerm)}`);
  
  if (!response.ok) {
    throw new Error(`Error searching users: ${response.status}`);
  }
  
  return await response.json();
}

// Create a new user
export async function createUser(userData: CreateUserRequest): Promise<User> {
  const response = await fetch(`${API_URL}/api/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    throw new Error(`Error creating user: ${response.status}`);
  }
  
  return await response.json();
}

// Update a user
export async function updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
  const response = await fetch(`${API_URL}/api/users/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    throw new Error(`Error updating user: ${response.status}`);
  }
  
  return await response.json();
}

// Update a user's password
export async function updatePassword(userId: number, passwordData: UpdatePasswordRequest): Promise<User> {
  const response = await fetch(`${API_URL}/api/users/${userId}/password`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(passwordData),
  });
  
  if (!response.ok) {
    throw new Error(`Error updating password: ${response.status}`);
  }
  
  return await response.json();
}

// Delete a user
export async function deleteUser(userId: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/users/${userId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Error deleting user: ${response.status}`);
  }
}

// Assign a role to a user
export async function assignRoleToUser(userId: number, roleId: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/users/${userId}/roles/${roleId}`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error(`Error assigning role: ${response.status}`);
  }
}

// Remove a role from a user
export async function removeRoleFromUser(userId: number, roleId: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/users/${userId}/roles/${roleId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Error removing role: ${response.status}`);
  }
}

// Get roles for a user
export async function fetchUserRoles(userId: number): Promise<Role[]> {
  const response = await fetch(`${API_URL}/api/users/${userId}/roles`);
  
  if (!response.ok) {
    throw new Error(`Error fetching user roles: ${response.status}`);
  }
  
  return await response.json();
}