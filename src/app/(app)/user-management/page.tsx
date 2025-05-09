import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MoreHorizontal, PlusCircle, Search, Trash2, Edit3, UserCog, ShieldCheck, Users } from "lucide-react";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// Mock data - replace with actual data fetching
const mockUsers = [
  { id: 'usr001', name: 'Admin User', email: 'admin@stepmedia.com', role: 'Administrator', status: 'Active', lastLogin: '2024-07-29 10:00 AM', avatarUrl: 'https://picsum.photos/seed/admin/40/40' },
  { id: 'usr002', name: 'HR Manager', email: 'hr.manager@example.com', role: 'HR Manager', status: 'Active', lastLogin: '2024-07-29 09:30 AM', avatarUrl: 'https://picsum.photos/seed/hr/40/40' },
  { id: 'usr003', name: 'Team Lead', email: 'team.lead@example.com', role: 'Team Lead', status: 'Inactive', lastLogin: '2024-07-20 15:00 PM', avatarUrl: 'https://picsum.photos/seed/lead/40/40' },
];

const mockRoles = [
  { id: 'role001', name: 'Administrator', description: 'Full access to all system features.', userCount: 1 },
  { id: 'role002', name: 'HR Manager', description: 'Manages employee data, leave, and attendance.', userCount: 1 },
  { id: 'role003', name: 'Team Lead', description: 'Can view team attendance and approve basic requests.', userCount: 5 },
  { id: 'role004', name: 'Employee', description: 'Standard access for employees to view their own data.', userCount: 50 },
];

export default function UserManagementPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <UserCog className="h-8 w-8 text-primary" /> User & Role Management
          </h1>
          <p className="text-muted-foreground">Manage users, their roles, and system permissions.</p>
        </div>
      </div>

      {/* Users Section */}
      <Card className="shadow-xl">
        <CardHeader className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 p-4 border-b">
          <CardTitle className="text-xl flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" /> System Users ({mockUsers.length})
          </CardTitle>
          <div className="flex gap-2 items-center w-full md:w-auto">
            <div className="relative flex-grow md:flex-grow-0">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search users..." className="pl-8 w-full md:w-[200px] lg:w-[250px]" />
            </div>
            <Button className="shadow-md hover:shadow-lg transition-shadow">
              <PlusCircle className="mr-2 h-5 w-5" /> Add User
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]">Avatar</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead className="text-right w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockUsers.map((user) => (
                  <TableRow key={user.id} className="hover:bg-muted/50 transition-colors">
                    <TableCell>
                      <Avatar className="h-8 w-8 border">
                        <AvatarImage src={user.avatarUrl} alt={user.name} data-ai-hint="person avatar" />
                        <AvatarFallback>{user.name.substring(0,1)}</AvatarFallback>
                      </Avatar>
                    </TableCell>
                    <TableCell className="font-medium">{user.name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{user.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.status === 'Active' ? 'default' : 'destructive'}
                       className={user.status === 'Active' ? 'bg-green-500/20 text-green-700 dark:bg-green-500/30 dark:text-green-400 border-green-500/30' : 'bg-red-500/20 text-red-700 dark:bg-red-500/30 dark:text-red-400 border-red-500/30'}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{user.lastLogin}</TableCell>
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
                            <Edit3 className="mr-2 h-4 w-4" /> Edit User
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <ShieldCheck className="mr-2 h-4 w-4" /> Change Role
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive focus:text-destructive focus:bg-destructive/10">
                            <Trash2 className="mr-2 h-4 w-4" /> Delete User
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Roles & Permissions Section */}
      <Card className="shadow-xl">
        <CardHeader className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 p-4 border-b">
          <CardTitle className="text-xl flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" /> Roles & Permissions ({mockRoles.length})
          </CardTitle>
           <div className="flex gap-2 items-center w-full md:w-auto">
            <div className="relative flex-grow md:flex-grow-0">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search roles..." className="pl-8 w-full md:w-[200px] lg:w-[250px]" />
            </div>
            <Button className="shadow-md hover:shadow-lg transition-shadow">
              <PlusCircle className="mr-2 h-5 w-5" /> Add Role
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
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
                {mockRoles.map((role) => (
                  <TableRow key={role.id} className="hover:bg-muted/50 transition-colors">
                    <TableCell className="font-medium">{role.name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{role.description}</TableCell>
                    <TableCell>{role.userCount}</TableCell>
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
                          <DropdownMenuItem className="text-destructive focus:text-destructive focus:bg-destructive/10">
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
