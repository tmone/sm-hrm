'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import EmployeeRegistration from './components/EmployeeRegistration';
import VideoProcessing from './components/VideoProcessing';
import IdentityManagement from './components/IdentityManagement';

export default function FacialRecognitionPage() {
  const [activeTab, setActiveTab] = useState<string>('employees');
  
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      <div>
        <h1 className="text-3xl font-bold">Facial Recognition</h1>
        <p className="text-muted-foreground mt-1">
          Manage employee face registrations, process videos, and organize identities
        </p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-3 w-[400px]">
          <TabsTrigger value="employees">Employees</TabsTrigger>
          <TabsTrigger value="videos">Videos</TabsTrigger>
          <TabsTrigger value="identities">Identities</TabsTrigger>
        </TabsList>
        
        <TabsContent value="employees" className="space-y-4">
          <EmployeeRegistration />
        </TabsContent>
        
        <TabsContent value="videos" className="space-y-4">
          <VideoProcessing />
        </TabsContent>
        
        <TabsContent value="identities" className="space-y-4">
          <IdentityManagement />
        </TabsContent>
      </Tabs>
    </div>
  );
}