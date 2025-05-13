import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, XCircle, Search, UserCheck, UserX, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { RegisteredFace, Employee } from '../../types';
import { API_CONFIG } from '../../config';
import EmployeeTable from './EmployeeTable';
import RegistrationStats from './RegistrationStats';
import { useToast } from '@/hooks/use-toast';

export default function EmployeeRegistration() {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'pending' | 'rejected'>('all');
  const [registeredFaces, setRegisteredFaces] = useState<RegisteredFace[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('');
  const [uploadedPhoto, setUploadedPhoto] = useState<File | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  
  // Fetch employees and registered faces on component mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch employees from the real API
        const employeesResponse = await fetch(`${API_CONFIG.baseUrl}/employees`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          },
          mode: API_CONFIG.corsMode,
          credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin'
        });
        
        if (!employeesResponse.ok) {
          throw new Error('Failed to fetch employees');
        }
        
        const employeesData = await employeesResponse.json();
        setEmployees(Array.isArray(employeesData) ? employeesData : []);
        
        // Fetch registered faces from the real API
        const facesResponse = await fetch(`${API_CONFIG.baseUrl}/registered-faces`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          },
          mode: API_CONFIG.corsMode,
          credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin'
        });
        
        if (!facesResponse.ok) {
          throw new Error('Failed to fetch registered faces');
        }
        
        const facesData = await facesResponse.json();
        setRegisteredFaces(Array.isArray(facesData) ? facesData : []);
      } catch (error) {
        console.error('Error fetching data:', error);
        // No toast notification for failed data load
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [toast]);
  
  // Create a mapping of employeeId to registration status
  const employeeFaceRegistrationMap = useMemo(() => {
    const map = new Map<string, RegisteredFace>();
    registeredFaces.forEach(face => {
      if (!map.has(face.employeeId) || 
          (map.get(face.employeeId)?.status !== 'Approved' && face.status === 'Approved')) {
        map.set(face.employeeId, face);
      }
    });
    return map;
  }, [registeredFaces]);

  // Get registered employees
  const registeredEmployees = useMemo(() => {
    return employees
      .filter(emp => employeeFaceRegistrationMap.has(emp.id))
      .map(emp => {
        const faceData = employeeFaceRegistrationMap.get(emp.id);
        return {
          ...emp,
          faceStatus: faceData?.status || null,
          faceRegisteredDate: faceData?.registeredDate || null,
          faceImageUrl: faceData?.imageUrl || null
        };
      });
  }, [employees, employeeFaceRegistrationMap]);

  // Get non-registered employees for the dropdown
  const nonRegisteredEmployees = useMemo(() => {
    return employees.filter(emp => !employeeFaceRegistrationMap.has(emp.id));
  }, [employees, employeeFaceRegistrationMap]);

  // Filter registered employees based on search and status
  const filteredEmployees = useMemo(() => {
    return registeredEmployees.filter(emp => {
      const matchesSearch = searchQuery === '' ||
        emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (emp.department && emp.department.toLowerCase().includes(searchQuery.toLowerCase())) ||
        emp.id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === 'all' ||
        (emp.faceStatus?.toLowerCase() === statusFilter);

      return matchesSearch && matchesStatus;
    });
  }, [registeredEmployees, searchQuery, statusFilter]);

  // Calculate stats
  const stats = useMemo(() => {
    const total = registeredEmployees.length;
    const approved = registeredEmployees.filter(emp => emp.faceStatus === 'Approved').length;
    const pending = registeredEmployees.filter(emp => emp.faceStatus === 'Pending').length;
    const rejected = registeredEmployees.filter(emp => emp.faceStatus === 'Rejected').length;
    
    return { total, approved, pending, rejected };
  }, [registeredEmployees]);

  // Handle photo upload
  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedPhoto(e.target.files[0]);
    }
  };

  // Handle face registration submission
  const handleRegisterFace = async () => {
    if (!selectedEmployeeId || !uploadedPhoto) {
      toast({
        title: 'Missing information',
        description: 'Please select an employee and upload a photo',
        variant: 'destructive'
      });
      return;
    }

    setIsRegistering(true);
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('employeeId', selectedEmployeeId);
      formData.append('photo', uploadedPhoto);
      
      // Send to real API
      const response = await fetch(`${API_CONFIG.baseUrl}/register-face`, {
        method: 'POST',
        body: formData,
        mode: API_CONFIG.corsMode,
        credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin'
      });
      
      if (!response.ok) {
        throw new Error('Failed to register face');
      }
      
      const data = await response.json();
      
      // Add the newly registered face to the state
      setRegisteredFaces(prev => [data.face, ...prev]);
      
      toast({
        title: 'Face registered successfully',
        description: 'The face has been registered and is pending approval',
      });
      
      // Close dialog and reset form
      setIsDialogOpen(false);
      setSelectedEmployeeId('');
      setUploadedPhoto(null);
    } catch (error) {
      console.error('Error registering face:', error);
      toast({
        title: 'Registration failed',
        description: 'There was an error registering the employee face',
        variant: 'destructive'
      });
    } finally {
      setIsRegistering(false);
    }
  };

  // Approve a face registration
  const handleApproveFace = async (employeeId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}/approve-face/${employeeId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: API_CONFIG.corsMode,
        credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin'
      });
      
      if (!response.ok) {
        throw new Error('Failed to approve face');
      }
      
      // Update the face status in the state
      setRegisteredFaces(prev => 
        prev.map(face => 
          face.employeeId === employeeId 
            ? { ...face, status: 'Approved' } 
            : face
        )
      );
      
      toast({
        title: 'Face approved',
        description: 'The employee face has been approved for recognition'
      });
    } catch (error) {
      console.error('Error approving face:', error);
      toast({
        title: 'Approval failed',
        description: 'There was an error approving the employee face',
        variant: 'destructive'
      });
    }
  };

  // Reject a face registration
  const handleRejectFace = async (employeeId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}/reject-face/${employeeId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: API_CONFIG.corsMode,
        credentials: API_CONFIG.withCredentials ? 'include' : 'same-origin'
      });
      
      if (!response.ok) {
        throw new Error('Failed to reject face');
      }
      
      // Update the face status in the state
      setRegisteredFaces(prev => 
        prev.map(face => 
          face.employeeId === employeeId 
            ? { ...face, status: 'Rejected' } 
            : face
        )
      );
      
      toast({
        title: 'Face rejected',
        description: 'The employee face has been rejected'
      });
    } catch (error) {
      console.error('Error rejecting face:', error);
      toast({
        title: 'Rejection failed',
        description: 'There was an error rejecting the employee face',
        variant: 'destructive'
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-lg">Loading employee data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Employee Face Registration</h2>
        <Button onClick={() => setIsDialogOpen(true)}>Register New Employee</Button>
      </div>

      <RegistrationStats stats={stats} />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Registered Employees</CardTitle>
          <CardDescription>Employees with facial recognition access</CardDescription>
          
          <div className="flex flex-col gap-4 mt-4 md:flex-row">
            <div className="flex-1">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  type="search"
                  placeholder="Search by name, ID, or department..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
            
            <div className="w-full md:w-[180px]">
              <Label htmlFor="status-filter">Filter by Status</Label>
              <Select 
                value={statusFilter} 
                onValueChange={(value) => setStatusFilter(value as any)}
              >
                <SelectTrigger id="status-filter">
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <EmployeeTable 
            employees={filteredEmployees} 
            onApprove={handleApproveFace}
            onReject={handleRejectFace}
          />
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Register Employee Face</DialogTitle>
            <DialogDescription>
              Upload a clear photo of the employee's face for registration.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="employee">Select Employee</Label>
              <Select 
                value={selectedEmployeeId} 
                onValueChange={setSelectedEmployeeId}
              >
                <SelectTrigger id="employee">
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {nonRegisteredEmployees.map(emp => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.name} ({emp.id})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="face-photo">Face Photo</Label>
              <input
                type="file"
                id="face-photo"
                accept="image/*"
                className="hidden"
                onChange={handlePhotoChange}
              />
              
              {uploadedPhoto ? (
                <div className="border rounded-lg p-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <p className="font-medium truncate">{uploadedPhoto.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {Math.round(uploadedPhoto.size / 1024)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setUploadedPhoto(null)}
                    className="mt-3 text-xs text-primary hover:underline"
                  >
                    Change photo
                  </button>
                </div>
              ) : (
                <div 
                  className="flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg h-44 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => document.getElementById('face-photo')?.click()}
                >
                  <div className="text-center">
                    <UserCheck className="mx-auto h-8 w-8 text-muted-foreground" />
                    <div className="mt-2">
                      <Button variant="outline" size="sm" type="button">
                        Select Photo
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      JPG, PNG or WEBP. Max 5MB.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsDialogOpen(false)}
              disabled={isRegistering}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleRegisterFace}
              disabled={!selectedEmployeeId || !uploadedPhoto || isRegistering}
            >
              {isRegistering ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Registering...
                </>
              ) : (
                'Register'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}