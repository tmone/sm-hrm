/**
 * Leave API functions for fetching real data from the backend
 */

import { LeaveRequest } from '@/types';
import { fetchFromApi, createApiUrl } from './utils';

// For backwards compatibility in specific fetch options
const API_CORS_MODE = (process.env.NEXT_PUBLIC_API_CORS_MODE || 'same-origin') as RequestMode;
const API_WITH_CREDENTIALS = process.env.NEXT_PUBLIC_API_WITH_CREDENTIALS === 'true';

/**
 * Fetch all leave requests
 */
export async function fetchLeaveRequests(): Promise<LeaveRequest[]> {
  try {
    const data = await fetchFromApi('api/leave-requests');
    return Array.isArray(data) ? data : (data.requests || []);
  } catch (error) {
    console.error('Error fetching leave requests:', error);
    return [];
  }
}

/**
 * Fetch leave requests for a specific employee
 */
export async function fetchEmployeeLeaveRequests(employeeId: string): Promise<LeaveRequest[]> {
  try {
    const data = await fetchFromApi(`api/leave-requests/employee/${employeeId}`);
    return Array.isArray(data) ? data : (data.requests || []);
  } catch (error) {
    console.error(`Error fetching leave requests for employee ${employeeId}:`, error);
    return [];
  }
}

/**
 * Create a new leave request
 */
export async function createLeaveRequest(request: Omit<LeaveRequest, 'id'>): Promise<LeaveRequest | null> {
  try {
    const url = createApiUrl('api/leave-requests');
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(request),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating leave request:', error);
    return null;
  }
}

/**
 * Update a leave request (e.g., approve or reject)
 */
export async function updateLeaveRequest(
  requestId: string, 
  updates: Partial<LeaveRequest>
): Promise<LeaveRequest | null> {
  try {
    const url = createApiUrl(`api/leave-requests/${requestId}`);
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(updates),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error updating leave request ${requestId}:`, error);
    return null;
  }
}

/**
 * Approve a leave request
 */
export async function approveLeaveRequest(
  requestId: string,
  approverId: string
): Promise<LeaveRequest | null> {
  try {
    const url = createApiUrl(`api/leave-requests/${requestId}/approve`);
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ approverId }),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error approving leave request ${requestId}:`, error);
    return null;
  }
}

/**
 * Reject a leave request
 */
export async function rejectLeaveRequest(
  requestId: string,
  reason?: string
): Promise<LeaveRequest | null> {
  try {
    const url = createApiUrl(`api/leave-requests/${requestId}/reject`);
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ reason }),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error rejecting leave request ${requestId}:`, error);
    return null;
  }
}

/**
 * Delete a leave request
 */
export async function deleteLeaveRequest(requestId: string): Promise<boolean> {
  try {
    const url = createApiUrl(`api/leave-requests/${requestId}`);
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
    console.error(`Error deleting leave request ${requestId}:`, error);
    return false;
  }
}