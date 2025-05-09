import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Check, Bell, UserCog } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight text-foreground">Settings</h1>
      <p className="text-muted-foreground">Manage your application and account settings.</p>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="shadow-lg lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5 text-primary" />
              Account Settings
            </CardTitle>
            <CardDescription>Update your personal information and preferences.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">First Name</Label>
                <Input id="firstName" defaultValue="Admin" />
              </div>
              <div>
                <Label htmlFor="lastName">Last Name</Label>
                <Input id="lastName" defaultValue="User" />
              </div>
            </div>
            <div>
              <Label htmlFor="email">Email Address</Label>
              <Input id="email" type="email" defaultValue="admin@stepmedia.com" />
            </div>
            <div>
              <Label htmlFor="password">New Password</Label>
              <Input id="password" type="password" placeholder="Enter new password (optional)" />
            </div>
            <Button className="w-full sm:w-auto shadow-md hover:shadow-lg transition-shadow">
              <Check className="mr-2 h-5 w-5" /> Update Profile
            </Button>
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary" />
              Notification Settings
            </CardTitle>
            <CardDescription>Manage how you receive notifications.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between space-x-2 p-2 rounded-md hover:bg-muted/50 transition-colors">
              <Label htmlFor="emailNotifications" className="cursor-pointer flex-grow">
                Email Notifications
                <p className="text-xs text-muted-foreground">Receive updates via email.</p>
              </Label>
              <Switch id="emailNotifications" defaultChecked />
            </div>
             <div className="flex items-center justify-between space-x-2 p-2 rounded-md hover:bg-muted/50 transition-colors">
              <Label htmlFor="pushNotifications" className="cursor-pointer flex-grow">
                Push Notifications
                <p className="text-xs text-muted-foreground">Get alerts directly on your device.</p>
              </Label>
              <Switch id="pushNotifications" />
            </div>
            <div className="flex items-center justify-between space-x-2 p-2 rounded-md hover:bg-muted/50 transition-colors">
              <Label htmlFor="leaveAlerts" className="cursor-pointer flex-grow">
                Leave Request Alerts
                <p className="text-xs text-muted-foreground">Notify on new leave requests or status changes.</p>
              </Label>
              <Switch id="leaveAlerts" defaultChecked />
            </div>
          </CardContent>
        </Card>
      </div>
       <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>System Configuration (Admin only - Placeholder)</CardTitle>
            <CardDescription>Global settings for the HRM system.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
             <p className="text-muted-foreground">This section would contain options for configuring workdays, holidays, leave policies, etc.</p>
             <Button variant="outline" disabled>Configure Policies</Button>
          </CardContent>
        </Card>
    </div>
  );
}
