import type { Employee, AttendanceRecord, LeaveRequest } from '@/types';
import { Users, Briefcase, CalendarX, UserCheck, ScanFace } from 'lucide-react';

export const mockEmployees: Employee[] = [
  {
    id: 'emp001',
    firstName: 'Alice',
    lastName: 'Smith',
    name: 'Alice Smith',
    department: 'Engineering',
    position: 'Software Engineer',
    email: 'alice.smith@example.com',
    phone: '555-0101',
    hireDate: '2022-08-15',
    avatarUrl: 'https://picsum.photos/seed/alice/100/100',
    status: 'Active',
  },
  {
    id: 'emp002',
    firstName: 'Bob',
    lastName: 'Johnson',
    name: 'Bob Johnson',
    department: 'Marketing',
    position: 'Marketing Manager',
    email: 'bob.johnson@example.com',
    phone: '555-0102',
    hireDate: '2021-05-20',
    avatarUrl: 'https://picsum.photos/seed/bob/100/100',
    status: 'Active',
  },
  {
    id: 'emp003',
    firstName: 'Carol',
    lastName: 'Williams',
    name: 'Carol Williams',
    department: 'Sales',
    position: 'Sales Representative',
    email: 'carol.williams@example.com',
    phone: '555-0103',
    hireDate: '2023-01-10',
    avatarUrl: 'https://picsum.photos/seed/carol/100/100',
    status: 'On Leave',
  },
  {
    id: 'emp004',
    firstName: 'David',
    lastName: 'Brown',
    name: 'David Brown',
    department: 'Human Resources',
    position: 'HR Specialist',
    email: 'david.brown@example.com',
    phone: '555-0104',
    hireDate: '2020-11-01',
    status: 'Active',
  },
  {
    id: 'emp005',
    firstName: 'Eve',
    lastName: 'Davis',
    name: 'Eve Davis',
    department: 'Engineering',
    position: 'QA Engineer',
    email: 'eve.davis@example.com',
    phone: '555-0105',
    hireDate: '2022-09-01',
    avatarUrl: 'https://picsum.photos/seed/eve/100/100',
    status: 'Terminated',
  },
];

export const mockAttendance: AttendanceRecord[] = [
  {
    id: 'att001',
    employeeId: 'emp001',
    employeeName: 'Alice Smith',
    date: '2024-07-28',
    checkInTime: '2024-07-28T09:05:00Z',
    checkOutTime: '2024-07-28T17:30:00Z',
    status: 'Present',
  },
  {
    id: 'att002',
    employeeId: 'emp002',
    employeeName: 'Bob Johnson',
    date: '2024-07-28',
    checkInTime: '2024-07-28T08:50:00Z',
    checkOutTime: '2024-07-28T17:25:00Z',
    status: 'Present',
  },
  {
    id: 'att003',
    employeeId: 'emp003',
    employeeName: 'Carol Williams',
    date: '2024-07-28',
    status: 'On Leave',
    notes: 'Annual leave',
  },
  {
    id: 'att004',
    employeeId: 'emp004',
    employeeName: 'David Brown',
    date: '2024-07-28',
    checkInTime: '2024-07-28T09:35:00Z', // Late
    checkOutTime: '2024-07-28T18:00:00Z',
    status: 'Late',
  },
   {
    id: 'att005',
    employeeId: 'emp001',
    employeeName: 'Alice Smith',
    date: '2024-07-27',
    checkInTime: '2024-07-27T09:00:00Z',
    checkOutTime: '2024-07-27T17:32:00Z',
    status: 'Present',
  },
  {
    id: 'att006',
    employeeId: 'emp002',
    employeeName: 'Bob Johnson',
    date: '2024-07-27',
    status: 'Absent',
    notes: 'Sick leave reported'
  },
];

export const mockLeaveRequests: LeaveRequest[] = [
  {
    id: 'lr001',
    employeeId: 'emp003',
    employeeName: 'Carol Williams',
    leaveType: 'Annual',
    startDate: '2024-07-28',
    endDate: '2024-08-02',
    reason: 'Vacation',
    status: 'Approved',
    requestedDate: '2024-07-15T10:00:00Z',
    approvedBy: 'David Brown',
    approvedDate: '2024-07-16T14:00:00Z',
  },
  {
    id: 'lr002',
    employeeId: 'emp001',
    employeeName: 'Alice Smith',
    leaveType: 'Sick',
    startDate: '2024-08-05',
    endDate: '2024-08-05',
    reason: 'Feeling unwell',
    status: 'Pending',
    requestedDate: '2024-08-04T09:00:00Z',
  },
  {
    id: 'lr003',
    employeeId: 'emp002',
    employeeName: 'Bob Johnson',
    leaveType: 'Unpaid',
    startDate: '2024-09-01',
    endDate: '2024-09-05',
    reason: 'Personal matters',
    status: 'Rejected',
    requestedDate: '2024-07-20T11:00:00Z',
  },
];

// Add mock data for facial recognition stats
const mockTotalRegisteredFaces = 12;
const mockApprovedRegisteredFaces = 8;


export const dashboardSummaryMetrics = [
  { label: 'Total Employees', value: mockEmployees.filter(e => e.status !== 'Terminated').length, icon: Users, change: '+2 this month', changeType: 'positive' as const },
  { label: 'On Leave Today', value: mockAttendance.filter(a => a.date === new Date().toISOString().split('T')[0] && a.status === 'On Leave').length, icon: CalendarX, change: '-1 vs yesterday', changeType: 'negative' as const },
  { label: 'Present Today', value: mockAttendance.filter(a => a.date === new Date().toISOString().split('T')[0] && (a.status === 'Present' || a.status === 'Late')).length, icon: UserCheck, change: '+3 vs yesterday', changeType: 'positive' as const },
  { label: 'Pending Leave Requests', value: mockLeaveRequests.filter(lr => lr.status === 'Pending').length, icon: Briefcase, change: '', changeType: 'positive' as const },
  { label: 'Registered Faces', value: `${mockApprovedRegisteredFaces} / ${mockTotalRegisteredFaces}`, icon: ScanFace, description: 'Approved / Total', changeType: 'positive' as const },
];
