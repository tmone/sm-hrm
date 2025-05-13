'use client';

import React, { useState, useEffect } from 'react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { LeaveRequest } from "@/types";
import { cn } from "@/lib/utils";
import { CalendarIcon, CheckCircle, Clock, MoreHorizontal, Search, XCircle, FileText, Loader2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { format, isValid, parseISO, addDays } from 'date-fns';
import { fetchLeaveRequests, createLeaveRequest, approveLeaveRequest, rejectLeaveRequest } from '@/lib/leave-api';
import { fetchEmployees } from '@/lib/employees-api';
import { useToast } from "@/hooks/use-toast";

export default function LeavePage() {
  const { toast } = useToast();
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  
  // Form state
  const [selectedEmployee, setSelectedEmployee] = useState<string>("");
  const [leaveType, setLeaveType] = useState<string>("");
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [reason, setReason] = useState<string>("");

  // Load leave requests and employees on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // Load leave requests
        const requests = await fetchLeaveRequests();
        setLeaveRequests(requests);
        
        // Load employees
        const empData = await fetchEmployees();
        setEmployees(empData);
      } catch (error) {
        console.error('Error loading data:', error);
        toast({
          title: 'Failed to load data',
          description: 'There was an error fetching leave request data.',
          variant: 'destructive'
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [toast]);

  // Format date consistently
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = parseISO(dateString);
      return isValid(date) ? format(date, 'MMM dd, yyyy') : 'Invalid Date';
    } catch (error) {
      return 'Invalid Date';
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Form validation
    if (!selectedEmployee || !leaveType || !startDate || !endDate || !reason) {
      toast({
        title: 'Missing information',
        description: 'Please fill out all required fields.',
        variant: 'destructive'
      });
      return;
    }

    // Validate date range
    if (endDate < startDate) {
      toast({
        title: 'Invalid date range',
        description: 'End date must be on or after start date.',
        variant: 'destructive'
      });
      return;
    }

    setIsSubmitting(true);

    // Create the leave request object
    const newRequest = {
      employeeId: selectedEmployee,
      employeeName: employees.find(emp => emp.id === selectedEmployee)?.name || "",
      leaveType: leaveType as any,
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      reason: reason,
      status: 'Pending' as const,
      requestedDate: new Date().toISOString()
    };

    try {
      const result = await createLeaveRequest(newRequest);
      
      if (result) {
        // Add the new request to the list
        setLeaveRequests(prev => [result, ...prev]);
        
        toast({
          title: 'Leave request submitted',
          description: 'Your request has been sent for approval.',
          variant: 'default'
        });
        
        // Reset form
        setSelectedEmployee("");
        setLeaveType("");
        setStartDate(undefined);
        setEndDate(undefined);
        setReason("");
      } else {
        throw new Error('Failed to create leave request');
      }
    } catch (error) {
      console.error('Error submitting leave request:', error);
      toast({
        title: 'Submission failed',
        description: 'There was an error submitting your leave request.',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle request approval
  const handleApprove = async (requestId: string) => {
    try {
      const result = await approveLeaveRequest(requestId, "1"); // Using "1" as a default approver ID
      
      if (result) {
        // Update the request in the list
        setLeaveRequests(prev => 
          prev.map(req => req.id === requestId ? result : req)
        );
        
        toast({
          title: 'Request approved',
          description: 'The leave request has been approved.',
          variant: 'default'
        });
      } else {
        throw new Error('Failed to approve request');
      }
    } catch (error) {
      console.error('Error approving request:', error);
      toast({
        title: 'Approval failed',
        description: 'There was an error approving the leave request.',
        variant: 'destructive'
      });
    }
  };

  // Handle request rejection
  const handleReject = async (requestId: string) => {
    try {
      const result = await rejectLeaveRequest(requestId);
      
      if (result) {
        // Update the request in the list
        setLeaveRequests(prev => 
          prev.map(req => req.id === requestId ? result : req)
        );
        
        toast({
          title: 'Request rejected',
          description: 'The leave request has been rejected.',
          variant: 'default'
        });
      } else {
        throw new Error('Failed to reject request');
      }
    } catch (error) {
      console.error('Error rejecting request:', error);
      toast({
        title: 'Rejection failed',
        description: 'There was an error rejecting the leave request.',
        variant: 'destructive'
      });
    }
  };

  // Filter leave requests based on search query
  const filteredRequests = searchQuery
    ? leaveRequests.filter(request => 
        request.employeeName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        request.leaveType.toLowerCase().includes(searchQuery.toLowerCase()) ||
        request.status.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : leaveRequests;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-80">
        <div className="text-center space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading leave request data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Leave Management</h1>
          <p className="text-muted-foreground">Submit and manage time off requests.</p>
        </div>
      </div>

      <Card className="shadow-xl">
        <CardHeader className="border-b">
          <CardTitle>Submit Leave Request</CardTitle>
          <CardDescription>Fill out the form to request time off.</CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <form className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end" onSubmit={handleSubmit}>
            <div className="md:col-span-1">
              <Label htmlFor="employee">Employee</Label>
              <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                <SelectTrigger id="employee">
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map(emp => (
                    <SelectItem key={emp.id} value={emp.id}>{emp.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="leaveType">Leave Type</Label>
              <Select value={leaveType} onValueChange={setLeaveType}>
                <SelectTrigger id="leaveType">
                  <SelectValue placeholder="Select leave type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Annual">Annual</SelectItem>
                  <SelectItem value="Sick">Sick</SelectItem>
                  <SelectItem value="Unpaid">Unpaid</SelectItem>
                  <SelectItem value="Maternity">Maternity</SelectItem>
                  <SelectItem value="Paternity">Paternity</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="startDate">Start Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button 
                    variant={"outline"} 
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !startDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, 'PP') : <span>Pick start date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={startDate}
                    onSelect={setStartDate}
                    initialFocus
                    disabled={(date) => date < addDays(new Date(), -1)}
                  />
                </PopoverContent>
              </Popover>
            </div>
            <div>
              <Label htmlFor="endDate">End Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button 
                    variant={"outline"} 
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !endDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, 'PP') : <span>Pick end date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={endDate}
                    onSelect={setEndDate}
                    initialFocus
                    disabled={(date) => startDate ? date < startDate : date < addDays(new Date(), -1)}
                  />
                </PopoverContent>
              </Popover>
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="reason">Reason</Label>
              <Textarea 
                id="reason" 
                placeholder="Provide a reason for your leave request."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button 
                type="submit" 
                className="w-full sm:w-auto shadow-md hover:shadow-lg transition-shadow"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-5 w-5" /> Submit Request
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card className="shadow-xl">
        <CardHeader className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 p-4 border-b">
          <CardTitle className="text-xl">Leave Request Log</CardTitle>
           <div className="relative w-full md:w-auto">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              type="search" 
              placeholder="Search requests..." 
              className="pl-8 w-full md:w-[250px] lg:w-[300px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Leave Type</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead>End Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRequests.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-40 text-center text-muted-foreground">
                      {searchQuery ? (
                        <div>
                          <p>No leave requests found matching "{searchQuery}"</p>
                          <Button 
                            variant="link" 
                            onClick={() => setSearchQuery('')}
                          >
                            Clear search
                          </Button>
                        </div>
                      ) : (
                        <p>No leave requests found.</p>
                      )}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRequests.map((request) => (
                    <TableRow key={request.id} className="hover:bg-muted/50 transition-colors">
                      <TableCell className="font-medium">{request.employeeName}</TableCell>
                      <TableCell>{request.leaveType}</TableCell>
                      <TableCell>{formatDate(request.startDate)}</TableCell>
                      <TableCell>{formatDate(request.endDate)}</TableCell>
                      <TableCell>
                        <Badge
                          variant={request.status === 'Approved' ? 'default' : request.status === 'Pending' ? 'outline' : 'destructive'}
                          className={cn(
                            request.status === 'Approved' && 'bg-green-500/20 text-green-700 dark:bg-green-500/30 dark:text-green-400 border-green-500/30',
                            request.status === 'Pending' && 'bg-yellow-500/20 text-yellow-700 dark:bg-yellow-500/30 dark:text-yellow-400 border-yellow-500/30',
                            request.status === 'Rejected' && 'bg-red-500/20 text-red-700 dark:bg-red-500/30 dark:text-red-400 border-red-500/30'
                          )}
                        >
                          {request.status === 'Approved' && <CheckCircle className="mr-1 h-3 w-3" />}
                          {request.status === 'Pending' && <Clock className="mr-1 h-3 w-3" />}
                          {request.status === 'Rejected' && <XCircle className="mr-1 h-3 w-3" />}
                          {request.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                               <span className="sr-only">Actions</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>View Details</DropdownMenuItem>
                            {request.status === 'Pending' && (
                              <DropdownMenuItem onClick={() => handleApprove(request.id)}>
                                Approve
                              </DropdownMenuItem>
                            )}
                            {request.status === 'Pending' && (
                              <DropdownMenuItem 
                                className="text-destructive focus:text-destructive focus:bg-destructive/10"
                                onClick={() => handleReject(request.id)}
                              >
                                Reject
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}