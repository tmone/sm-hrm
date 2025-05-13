/**
 * Attendance API functions for fetching real data from the backend
 */

import { AttendanceRecord } from '@/types';
import { fetchFromApi, createApiUrl } from './utils';

// For backwards compatibility in specific fetch options
const API_CORS_MODE = (process.env.NEXT_PUBLIC_API_CORS_MODE || 'same-origin') as RequestMode;
const API_WITH_CREDENTIALS = process.env.NEXT_PUBLIC_API_WITH_CREDENTIALS === 'true';

/**
 * Fetch all attendance records
 */
export async function fetchAttendanceRecords(): Promise<AttendanceRecord[]> {
  try {
    const data = await fetchFromApi('api/attendance');
    return Array.isArray(data) ? data : (data.records || []);
  } catch (error) {
    console.error('Error fetching attendance records:', error);
    return [];
  }
}

/**
 * Fetch attendance records for a specific date
 */
export async function fetchAttendanceByDate(date: string): Promise<AttendanceRecord[]> {
  try {
    const data = await fetchFromApi(`api/attendance/date/${date}`);
    return Array.isArray(data) ? data : (data.records || []);
  } catch (error) {
    console.error(`Error fetching attendance for date ${date}:`, error);
    return [];
  }
}

/**
 * Create a new attendance record
 */
export async function createAttendanceRecord(record: Omit<AttendanceRecord, 'id'>): Promise<AttendanceRecord | null> {
  try {
    const url = createApiUrl('api/attendance');
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(record),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating attendance record:', error);
    return null;
  }
}

/**
 * Update an existing attendance record
 */
export async function updateAttendanceRecord(id: string, record: Partial<AttendanceRecord>): Promise<AttendanceRecord | null> {
  try {
    const url = createApiUrl(`api/attendance/${id}`);
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(record),
      mode: API_CORS_MODE,
      credentials: API_WITH_CREDENTIALS ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`API response error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error updating attendance record ${id}:`, error);
    return null;
  }
}

/**
 * Delete an attendance record
 */
export async function deleteAttendanceRecord(id: string): Promise<boolean> {
  try {
    const url = createApiUrl(`api/attendance/${id}`);
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
    console.error(`Error deleting attendance record ${id}:`, error);
    return false;
  }
}