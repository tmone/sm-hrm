'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import EmployeeRegistration from './components/EmployeeRegistration';
import VideoProcessing from './components/VideoProcessing';
import VideoLabelingHub from './components/VideoLabelingHub';

export default function FacialRecognitionPage() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState<string>('employees');
  
  // Set the active tab based on URL param if present
  useEffect(() => {
    if (tabParam && ['employees', 'videos', 'labeling'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);
  
  return (
    <div className="container mx-auto py-6 space-y-6 max-w-7xl">
      <div>
        <h1 className="text-3xl font-bold">Facial Recognition</h1>
        <p className="text-muted-foreground mt-1">
          Manage employee face registrations, process videos, and label detected faces
        </p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-3 w-[400px]">
          <TabsTrigger value="employees">Employees</TabsTrigger>
          <TabsTrigger value="videos">Videos</TabsTrigger>
          <TabsTrigger value="labeling">Face Labeling</TabsTrigger>
        </TabsList>
        
        <TabsContent value="employees" className="space-y-4">
          <EmployeeRegistration />
        </TabsContent>
        
        <TabsContent value="videos" className="space-y-4">
          <VideoProcessing />
        </TabsContent>
        
        <TabsContent value="labeling" className="space-y-4">
          <VideoLabelingHub />
        </TabsContent>
      </Tabs>
    </div>
  );
}