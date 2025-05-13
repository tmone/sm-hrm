/**
 * Employees API functions for fetching real data from the backend
 */

import { Employee } from '@/types';
import { fetchFromApi, createApiUrl } from './utils';

// For backwards compatibility in specific fetch options
const API_CORS_MODE = (process.env.NEXT_PUBLIC_API_CORS_MODE || 'same-origin') as RequestMode;
const API_WITH_CREDENTIALS = process.env.NEXT_PUBLIC_API_WITH_CREDENTIALS === 'true';

/**
 * Fetch all employees from the backend
 */
export async function fetchEmployees(): Promise<Employee[]> {
  try {
    const data = await fetchFromApi('api/employees');
    // Return the employees array from the response, or an empty array if not found
    return Array.isArray(data) ? data : (data.employees || []);
  } catch (error) {
    console.error('Error fetching employees:', error);
    return [];
  }
}

/**
 * Search employees by name, department, position, etc.
 */
export async function searchEmployees(query: string): Promise<Employee[]> {
  try {
    const data = await fetchFromApi(`api/employees/search?q=${encodeURIComponent(query)}`);
    return Array.isArray(data) ? data : (data.employees || []);
  } catch (error) {
    console.error('Error searching employees:', error);
    return [];
  }
}

/**
 * Fetch a single employee by ID
 */
export async function fetchEmployeeById(id: string): Promise<Employee | null> {
  try {
    const data = await fetchFromApi(`api/employees/${id}`);
    return data || null;
  } catch (error) {
    console.error(`Error fetching employee ${id}:`, error);
    return null;
  }
}

/**
 * Create a new employee
 */
export async function createEmployee(employee: Omit<Employee, 'id'>): Promise<Employee | null> {
  try {
    const url = createApiUrl('api/employees');
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(employee),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating employee:', error);
    return null;
  }
}

/**
 * Update an existing employee
 */
export async function updateEmployee(id: string, employee: Partial<Employee>): Promise<Employee | null> {
  try {
    const url = createApiUrl(`api/employees/${id}`);
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(employee),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error updating employee ${id}:`, error);
    return null;
  }
}

/**
 * Delete an employee
 */
export async function deleteEmployee(id: string): Promise<boolean> {
  try {
    const url = createApiUrl(`api/employees/${id}`);
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json'
      },
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return true;
  } catch (error) {
    console.error(`Error deleting employee ${id}:`, error);
    return false;
  }
}