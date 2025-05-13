/**
 * Dashboard API functions for fetching real data from the backend
 */
import { fetchFromApi } from './utils';

/**
 * Fetch dashboard summary metrics from the backend
 */
export async function fetchDashboardSummary() {
  try {
    const data = await fetchFromApi('api/dashboard/summary');
    return data;
  } catch (error) {
    console.error('Error fetching dashboard summary:', error);
    return {
      totalEmployees: 0,
      onLeaveToday: 0,
      presentToday: 0,
      pendingLeaveRequests: 0,
      registeredFaces: {
        approved: 0,
        total: 0
      }
    };
  }
}

/**
 * Fetch today's attendance records from the backend
 */
export async function fetchTodayAttendance() {
  try {
    const data = await fetchFromApi('api/attendance/today');
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('Error fetching today\'s attendance:', error);
    return [];
  }
}

/**
 * Fetch upcoming approved leaves from the backend
 */
export async function fetchUpcomingLeaves() {
  try {
    const data = await fetchFromApi('api/leaves/upcoming');
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('Error fetching upcoming leaves:', error);
    return [];
  }
}

/**
 * Fetch attendance data for the upcoming days
 */
export async function fetchUpcomingAbsencesData() {
  try {
    const data = await fetchFromApi('api/leaves/upcoming-absences');
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('Error fetching upcoming absences data:', error);
    return [];
  }
}