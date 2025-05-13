import { API_URL } from './constants';
import { Role } from './users-api';

export interface RoleWithUserCount extends Role {
  user_count: number;
}

export interface CreateRoleRequest {
  name: string;
  description?: string;
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
}

// Get all roles
export async function fetchRoles(): Promise<Role[]> {
  const response = await fetch(`${API_URL}/api/roles`);
  
  if (!response.ok) {
    throw new Error(`Error fetching roles: ${response.status}`);
  }
  
  return await response.json();
}

// Get all roles with user counts
export async function fetchRolesWithUserCounts(): Promise<RoleWithUserCount[]> {
  const response = await fetch(`${API_URL}/api/roles/with-user-counts`);
  
  if (!response.ok) {
    throw new Error(`Error fetching roles with user counts: ${response.status}`);
  }
  
  return await response.json();
}

// Get a role by ID
export async function fetchRoleById(roleId: number): Promise<Role> {
  const response = await fetch(`${API_URL}/api/roles/${roleId}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching role: ${response.status}`);
  }
  
  return await response.json();
}

// Search roles
export async function searchRoles(searchTerm: string): Promise<Role[]> {
  const response = await fetch(`${API_URL}/api/roles/search?q=${encodeURIComponent(searchTerm)}`);
  
  if (!response.ok) {
    throw new Error(`Error searching roles: ${response.status}`);
  }
  
  return await response.json();
}

// Create a new role
export async function createRole(roleData: CreateRoleRequest): Promise<Role> {
  const response = await fetch(`${API_URL}/api/roles`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(roleData),
  });
  
  if (!response.ok) {
    throw new Error(`Error creating role: ${response.status}`);
  }
  
  return await response.json();
}

// Update a role
export async function updateRole(roleId: number, roleData: UpdateRoleRequest): Promise<Role> {
  const response = await fetch(`${API_URL}/api/roles/${roleId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(roleData),
  });
  
  if (!response.ok) {
    throw new Error(`Error updating role: ${response.status}`);
  }
  
  return await response.json();
}

// Delete a role
export async function deleteRole(roleId: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/roles/${roleId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Error deleting role: ${response.status}`);
  }
}

// Get users with a specific role
export async function fetchUsersWithRole(roleId: number): Promise<any[]> {
  const response = await fetch(`${API_URL}/api/roles/${roleId}/users`);
  
  if (!response.ok) {
    throw new Error(`Error fetching users with role: ${response.status}`);
  }
  
  return await response.json();
}