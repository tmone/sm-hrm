'use client';

import React, { useState, useEffect } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { fetchEmployees, searchEmployees } from "@/lib/employees-api";
import type { Employee } from "@/types";
import { cn } from "@/lib/utils";
import { MoreHorizontal, PlusCircle, Search, Trash2, Edit3, UserCircle, Loader2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";

export default function EmployeesPage() {
  const { toast } = useToast();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);

  // Load employees on component mount
  useEffect(() => {
    const loadEmployees = async () => {
      try {
        setIsLoading(true);
        const data = await fetchEmployees();
        setEmployees(data);
      } catch (error) {
        console.error('Error loading employees:', error);
        toast({
          title: 'Failed to load employees',
          description: 'There was an error fetching employee data.',
          variant: 'destructive'
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadEmployees();
  }, [toast]);

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  // Handle search query submission
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // If search query is empty, load all employees
      try {
        setIsSearching(true);
        const data = await fetchEmployees();
        setEmployees(data);
      } catch (error) {
        console.error('Error loading employees:', error);
        toast({
          title: 'Failed to load employees',
          description: 'There was an error fetching employee data.',
          variant: 'destructive'
        });
      } finally {
        setIsSearching(false);
      }
      return;
    }

    try {
      setIsSearching(true);
      const data = await searchEmployees(searchQuery);
      setEmployees(data);
    } catch (error) {
      console.error('Error searching employees:', error);
      toast({
        title: 'Search failed',
        description: 'Failed to search for employees.',
        variant: 'destructive'
      });
    } finally {
      setIsSearching(false);
    }
  };

  // Handle Enter key press in search field
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-80">
        <div className="text-center space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading employee data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Employee Directory</h1>
          <p className="text-muted-foreground">View and manage employee details.</p>
        </div>
        <Button className="shadow-md hover:shadow-lg transition-shadow">
          <PlusCircle className="mr-2 h-5 w-5" /> Add Employee
        </Button>
      </div>

      <Card className="shadow-xl">
        <CardHeader className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 p-4 border-b">
          <CardTitle className="text-xl">All Employees ({employees.length})</CardTitle>
          <div className="relative w-full md:w-auto">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              type="search" 
              placeholder="Search employees..." 
              className="pl-8 w-full md:w-[250px] lg:w-[300px]"
              value={searchQuery}
              onChange={handleSearchChange}
              onKeyDown={handleKeyDown}
              disabled={isSearching} 
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            {isSearching ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                <span className="ml-2">Searching...</span>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Avatar</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Position</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employees.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-40 text-center text-muted-foreground">
                        {searchQuery ? (
                          <div>
                            <p>No employees found matching "{searchQuery}"</p>
                            <Button 
                              variant="link" 
                              onClick={() => {
                                setSearchQuery('');
                                handleSearch();
                              }}
                            >
                              Clear search
                            </Button>
                          </div>
                        ) : (
                          <p>No employees found in the database.</p>
                        )}
                      </TableCell>
                    </TableRow>
                  ) : (
                    employees.map((employee) => (
                      <TableRow key={employee.id} className="hover:bg-muted/50 transition-colors">
                        <TableCell>
                          <Avatar className="h-10 w-10 border">
                            <AvatarImage src={employee.avatarUrl} alt={employee.name} data-ai-hint="person photo" />
                            <AvatarFallback>
                              <UserCircle className="h-6 w-6 text-muted-foreground"/>
                            </AvatarFallback>
                          </Avatar>
                        </TableCell>
                        <TableCell className="font-medium">{employee.name}</TableCell>
                        <TableCell>{employee.department}</TableCell>
                        <TableCell>{employee.position}</TableCell>
                        <TableCell>{employee.email}</TableCell>
                        <TableCell>
                          <Badge variant={employee.status === 'Active' ? 'default' : employee.status === 'On Leave' ? 'outline' : 'destructive'}
                           className={cn(
                            employee.status === 'Active' && 'bg-green-500/20 text-green-700 dark:bg-green-500/30 dark:text-green-400 border-green-500/30',
                            employee.status === 'On Leave' && 'bg-blue-500/20 text-blue-700 dark:bg-blue-500/30 dark:text-blue-400 border-blue-500/30',
                            employee.status === 'Terminated' && 'bg-destructive/20 text-destructive dark:bg-destructive/30 border-destructive/30'
                           )}
                          >
                            {employee.status}
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
                              <DropdownMenuItem>
                                <Edit3 className="mr-2 h-4 w-4" /> Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem className="text-destructive focus:text-destructive focus:bg-destructive/10">
                                <Trash2 className="mr-2 h-4 w-4" /> Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}