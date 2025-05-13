'use client'

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MoreHorizontal, PlusCircle, Search, Trash2, Edit3, ShieldCheck, Loader2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { fetchRoles, fetchRolesWithUserCounts, searchRoles } from "@/lib/roles-api";
import { useToast } from "@/hooks/use-toast";

export default function RoleManagementPage() {
  const { toast } = useToast();
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  
  // Load roles on initial page load
  useEffect(() => {
    loadRoles();
  }, []);
  
  // Load all roles with user counts
  const loadRoles = async () => {
    try {
      setLoading(true);
      const data = await fetchRolesWithUserCounts();
      setRoles(data);
    } catch (error) {
      console.error("Error loading roles:", error);
      toast({
        title: "Error",
        description: "Failed to load roles. Please try again.",
        variant: "destructive",
      });
      
      // Fallback to regular roles endpoint (non-admin might not have access to user counts)
      try {
        const basicRoles = await fetchRoles();
        setRoles(basicRoles.map(role => ({
          ...role,
          user_count: 0, // Default user count if we can't get the real count
        })));
      } catch (fallbackError) {
        console.error("Fallback error loading roles:", fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  // Handle search form submit
  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchTerm.trim()) {
      return loadRoles();
    }
    
    try {
      setIsSearching(true);
      const results = await searchRoles(searchTerm);
      setRoles(results.map(role => ({
        ...role,
        user_count: role.user_count || 0, // Ensure user_count exists
      })));
    } catch (error) {
      console.error("Error searching roles:", error);
      toast({
        title: "Search Error",
        description: "Failed to search roles. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ShieldCheck className="h-8 w-8 text-primary" /> Role Management
          </h1>
          <p className="text-muted-foreground">Manage system roles and their permissions.</p>
        </div>
      </div>

      {/* Roles & Permissions Section */}
      <Card className="shadow-xl">
        <CardHeader className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 p-4 border-b">
          <CardTitle className="text-xl flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" /> Roles & Permissions ({roles.length})
          </CardTitle>
          <div className="flex gap-2 items-center w-full md:w-auto">
            <form onSubmit={handleSearch} className="relative flex-grow md:flex-grow-0">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input 
                type="search" 
                placeholder="Search roles..." 
                className="pl-8 w-full md:w-[200px] lg:w-[250px]" 
                value={searchTerm}
                onChange={handleSearchChange}
              />
              {isSearching && (
                <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
              )}
            </form>
            <Button className="shadow-md hover:shadow-lg transition-shadow">
              <PlusCircle className="mr-2 h-5 w-5" /> Add Role
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="ml-2 text-muted-foreground">Loading roles...</span>
            </div>
          ) : roles.length === 0 ? (
            <div className="flex flex-col justify-center items-center h-64 text-center p-4">
              <ShieldCheck className="h-16 w-16 text-muted-foreground/30 mb-4" />
              <h3 className="font-medium text-lg">No Roles Found</h3>
              <p className="text-muted-foreground max-w-md mt-2">
                {searchTerm 
                  ? `No roles matching "${searchTerm}" were found. Try a different search term.` 
                  : "There are no roles in the system yet. Add a new role to get started."}
              </p>
              <Button className="mt-4" onClick={loadRoles}>
                Reset
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Users</TableHead>
                    <TableHead className="text-right w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roles.map((role) => (
                    <TableRow key={role.id} className="hover:bg-muted/50 transition-colors">
                      <TableCell className="font-medium">{role.name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{role.description || "No description provided"}</TableCell>
                      <TableCell>{role.user_count || 0}</TableCell>
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
                              <Edit3 className="mr-2 h-4 w-4" /> Edit Role
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <ShieldCheck className="mr-2 h-4 w-4" /> Manage Permissions
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-destructive focus:text-destructive focus:bg-destructive/10"
                              disabled={role.user_count > 0}
                            >
                              <Trash2 className="mr-2 h-4 w-4" /> Delete Role
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="shadow-xl">
        <CardHeader>
          <CardTitle className="text-xl">Permission Matrix (Placeholder)</CardTitle>
          <CardDescription>Detailed view of permissions assigned to each role for different modules.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">This section will display a matrix or detailed list of permissions for roles (e.g., Employee: Read Own Profile; HR Manager: Create/Edit/Delete Employee Profile, Approve Leave, etc.).</p>
        </CardContent>
      </Card>
    </div>
  );
}