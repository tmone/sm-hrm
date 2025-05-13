'use client'

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Check, Bell, UserCog, Loader2 } from "lucide-react";
import { fetchUserProfile, fetchUserSettings, updateUserProfile, updateUserSettings } from "@/lib/settings-api";
import { useToast } from "@/hooks/use-toast";

export default function SettingsPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    full_name: '',
    email: '',
    username: '',
    password: ''
  });
  const [settings, setSettings] = useState({
    email_notifications: true,
    push_notifications: false,
    leave_alerts: true
  });
  
  // Extract first and last name from full name for the form
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  
  // Load user profile and settings on page load
  useEffect(() => {
    async function loadUserData() {
      try {
        setLoading(true);
        
        // Load profile and settings in parallel
        const [profileData, settingsData] = await Promise.all([
          fetchUserProfile(),
          fetchUserSettings()
        ]);
        
        setProfile({
          ...profileData,
          password: ''
        });
        
        // Split full name into first and last name
        const nameParts = profileData.full_name.split(' ');
        setFirstName(nameParts[0] || '');
        setLastName(nameParts.slice(1).join(' ') || '');
        
        setSettings(settingsData);
      } catch (error) {
        console.error("Error loading user data:", error);
        toast({
          title: "Error",
          description: "Failed to load your profile data. Please refresh the page.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    }
    
    loadUserData();
  }, [toast]);
  
  // Handle form input changes
  const handleProfileChange = (e) => {
    const { id, value } = e.target;
    
    if (id === 'firstName') {
      setFirstName(value);
    } else if (id === 'lastName') {
      setLastName(value);
    } else {
      setProfile({
        ...profile,
        [id]: value
      });
    }
  };
  
  // Handle notification toggle changes
  const handleSettingChange = (id) => {
    setSettings({
      ...settings,
      [id]: !settings[id]
    });
  };
  
  // Save profile changes
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      
      // Combine first and last name into full name
      const profileData = {
        ...profile,
        full_name: `${firstName} ${lastName}`.trim(),
      };
      
      // Only send password if it's not empty
      if (!profileData.password) {
        delete profileData.password;
      }
      
      // Update profile
      await updateUserProfile(profileData);
      
      toast({
        title: "Success",
        description: "Your profile has been updated successfully.",
      });
      
      // Clear password field after update
      setProfile({
        ...profile,
        password: ''
      });
    } catch (error) {
      console.error("Error saving profile:", error);
      toast({
        title: "Error",
        description: "Failed to update your profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Save notification settings
  const handleSaveSettings = async () => {
    try {
      await updateUserSettings(settings);
      
      toast({
        title: "Success",
        description: "Your notification settings have been updated successfully.",
      });
    } catch (error) {
      console.error("Error saving settings:", error);
      toast({
        title: "Error",
        description: "Failed to update your notification settings. Please try again.",
        variant: "destructive",
      });
    }
  };
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Loading your settings...</p>
      </div>
    );
  }

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
            <form onSubmit={handleSaveProfile}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <Label htmlFor="firstName">First Name</Label>
                  <Input 
                    id="firstName" 
                    value={firstName} 
                    onChange={handleProfileChange} 
                    required 
                  />
                </div>
                <div>
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input 
                    id="lastName" 
                    value={lastName} 
                    onChange={handleProfileChange} 
                  />
                </div>
              </div>
              <div className="mb-4">
                <Label htmlFor="email">Email Address</Label>
                <Input 
                  id="email" 
                  type="email" 
                  value={profile.email} 
                  onChange={handleProfileChange} 
                  required 
                />
              </div>
              <div className="mb-4">
                <Label htmlFor="username">Username</Label>
                <Input 
                  id="username" 
                  value={profile.username} 
                  onChange={handleProfileChange} 
                  required 
                />
              </div>
              <div className="mb-4">
                <Label htmlFor="password">New Password</Label>
                <Input 
                  id="password" 
                  type="password" 
                  value={profile.password} 
                  onChange={handleProfileChange} 
                  placeholder="Enter new password (optional)" 
                />
              </div>
              <Button 
                type="submit" 
                className="w-full sm:w-auto shadow-md hover:shadow-lg transition-shadow"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Updating...
                  </>
                ) : (
                  <>
                    <Check className="mr-2 h-5 w-5" /> Update Profile
                  </>
                )}
              </Button>
            </form>
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
              <Switch 
                id="emailNotifications" 
                checked={settings.email_notifications} 
                onCheckedChange={() => handleSettingChange('email_notifications')}
              />
            </div>
            <div className="flex items-center justify-between space-x-2 p-2 rounded-md hover:bg-muted/50 transition-colors">
              <Label htmlFor="pushNotifications" className="cursor-pointer flex-grow">
                Push Notifications
                <p className="text-xs text-muted-foreground">Get alerts directly on your device.</p>
              </Label>
              <Switch 
                id="pushNotifications" 
                checked={settings.push_notifications} 
                onCheckedChange={() => handleSettingChange('push_notifications')}
              />
            </div>
            <div className="flex items-center justify-between space-x-2 p-2 rounded-md hover:bg-muted/50 transition-colors">
              <Label htmlFor="leaveAlerts" className="cursor-pointer flex-grow">
                Leave Request Alerts
                <p className="text-xs text-muted-foreground">Notify on new leave requests or status changes.</p>
              </Label>
              <Switch 
                id="leaveAlerts" 
                checked={settings.leave_alerts} 
                onCheckedChange={() => handleSettingChange('leave_alerts')}
              />
            </div>
            <Button 
              onClick={handleSaveSettings}
              className="w-full shadow-md hover:shadow-lg transition-shadow"
            >
              <Check className="mr-2 h-5 w-5" /> Save Notification Settings
            </Button>
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