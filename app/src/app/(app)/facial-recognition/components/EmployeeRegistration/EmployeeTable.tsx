import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, XCircle, UserCheck, UserX } from 'lucide-react';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { Employee } from '../../types';

interface EmployeeTableProps {
  employees: Employee[];
  onApprove?: (employeeId: string) => void;
  onReject?: (employeeId: string) => void;
}

export default function EmployeeTable({ employees, onApprove, onReject }: EmployeeTableProps) {
  const renderStatusBadge = (status: string | null) => {
    switch (status) {
      case 'Approved':
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <CheckCircle className="h-3.5 w-3.5 mr-1" />
            Approved
          </Badge>
        );
      case 'Pending':
        return (
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
            <Clock className="h-3.5 w-3.5 mr-1" />
            Pending
          </Badge>
        );
      case 'Rejected':
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
            <XCircle className="h-3.5 w-3.5 mr-1" />
            Rejected
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground">
            Not Registered
          </Badge>
        );
    }
  };

  return (
    <div className="rounded-md border">
      <div className="relative w-full overflow-auto">
        <table className="w-full caption-bottom text-sm">
          <thead className="[&_tr]:border-b">
            <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Employee</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Department</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">ID</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Registration Date</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody className="[&_tr:last-child]:border-0">
            {employees.length === 0 ? (
              <tr>
                <td colSpan={6} className="h-24 text-center text-muted-foreground">
                  No employees found matching the filter criteria.
                </td>
              </tr>
            ) : (
              employees.map((employee) => (
                <tr 
                  key={employee.id} 
                  className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                >
                  <td className="p-4 align-middle">
                    <div className="flex items-center gap-3">
                      <div className="relative h-10 w-10 overflow-hidden rounded-full">
                        {employee.faceImageUrl ? (
                          <Image 
                            src={employee.faceImageUrl} 
                            alt={employee.name}
                            fill
                            className="object-cover"
                          />
                        ) : (
                          <div className={cn(
                            "w-full h-full flex items-center justify-center rounded-full",
                            "bg-primary/10 text-primary font-medium"
                          )}>
                            {employee.name.substring(0, 2).toUpperCase()}
                          </div>
                        )}
                      </div>
                      <div>
                        <div className="font-medium">{employee.name}</div>
                        <div className="text-xs text-muted-foreground">{employee.position}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 align-middle">{employee.department}</td>
                  <td className="p-4 align-middle">{employee.id}</td>
                  <td className="p-4 align-middle">
                    {renderStatusBadge(employee.faceStatus)}
                  </td>
                  <td className="p-4 align-middle">
                    {employee.faceRegisteredDate || '—'}
                  </td>
                  <td className="p-4 align-middle">
                    <div className="flex items-center gap-2">
                      {employee.faceStatus === 'Pending' && (
                        <>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="h-8 gap-1"
                            onClick={() => onApprove?.(employee.id)}
                          >
                            <CheckCircle className="h-3.5 w-3.5" />
                            Approve
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="h-8 gap-1 text-red-600 border-red-200 hover:bg-red-50"
                            onClick={() => onReject?.(employee.id)}
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            Reject
                          </Button>
                        </>
                      )}
                      {employee.faceStatus === 'Approved' && (
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="h-8 gap-1 text-red-600 border-red-200 hover:bg-red-50"
                          onClick={() => onReject?.(employee.id)}
                        >
                          <UserX className="h-3.5 w-3.5" />
                          Revoke
                        </Button>
                      )}
                      {employee.faceStatus === 'Rejected' && (
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="h-8 gap-1"
                          onClick={() => onApprove?.(employee.id)}
                        >
                          <UserCheck className="h-3.5 w-3.5" />
                          Register Again
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}