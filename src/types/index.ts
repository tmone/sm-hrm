export interface Employee {
  id: string;
  name: string;
  firstName: string;
  lastName: string;
  department: string;
  position: string;
  email: string;
  phone: string;
  hireDate: string;
  avatarUrl?: string;
  status: 'Active' | 'On Leave' | 'Terminated';
}

export interface AttendanceRecord {
  id: string;
  employeeId: string;
  employeeName: string; // Denormalized for easier display
  date: string; // ISO date string
  checkInTime?: string; // ISO datetime string
  checkOutTime?: string; // ISO datetime string
  status: 'Present' | 'Absent' | 'Late' | 'On Leave';
  notes?: string;
}

export interface LeaveRequest {
  id: string;
  employeeId: string;
  employeeName: string; // Denormalized
  leaveType: 'Annual' | 'Sick' | 'Unpaid' | 'Maternity' | 'Paternity' | 'Other';
  startDate: string; // ISO date string
  endDate: string; // ISO date string
  reason: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  requestedDate: string; // ISO datetime string
  approvedBy?: string; // approver's ID or name
  approvedDate?: string; // ISO datetime string
}

export interface SummaryMetric {
  label: string;
  value: string | number;
  icon?: React.ElementType;
  change?: string; // e.g., "+5%" or "-2"
  changeType?: 'positive' | 'negative';
}
