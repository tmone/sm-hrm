'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Users,
  User,
  Calendar,
  Tag,
  UserCheck,
  UserX,
  Activity,
  CheckCircle2,
  AlertCircle,
  Brain,
  Loader2
} from 'lucide-react';
import { fetchFromAPI } from '../api';
import { useToast } from '@/hooks/use-toast';

interface LabeledFace {
  id: string;
  url: string;
  identity_id: string;
  label: string;
  employee_id: string | null;
  video_id: string;
  created_at: string;
}

interface IdentityGroup {
  id: string;
  name?: string;
  label?: string;
  employee_id: string | null;
  faces?: LabeledFace[];
  face_ids?: string[];
  created: string;
  created_at?: string;
  last_updated: string;
}

interface TrainingJob {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
}

export default function FaceLabelingGrid() {
  const router = useRouter();
  const { toast } = useToast();
  const [identityGroups, setIdentityGroups] = useState<IdentityGroup[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingJob, setTrainingJob] = useState<TrainingJob | null>(null);

  useEffect(() => {
    loadLabeledFaces();
  }, []);

  const loadLabeledFaces = async () => {
    try {
      setIsLoading(true);
      console.log('Loading identity groups...');
      const data = await fetchFromAPI('/api/identity-groups');
      console.log('Identity groups response:', data);

      if (data && data.groups) {
        // API returns {groups: [...]}, where groups is an array
        if (Array.isArray(data.groups)) {
          console.log(`Found ${data.groups.length} groups (array)`);
          setIdentityGroups(data.groups);
        } else if (typeof data.groups === 'object') {
          // If groups is an object, convert to array
          const groupsArray = Object.values(data.groups);
          console.log(`Found ${groupsArray.length} groups (object)`);
          setIdentityGroups(groupsArray);
        } else {
          console.log('Groups data is neither array nor object');
          setIdentityGroups([]);
        }
      } else if (data && Array.isArray(data)) {
        // Direct array response
        console.log(`Found ${data.length} groups (direct array)`);
        setIdentityGroups(data);
      } else {
        console.log('No valid groups data found');
        setIdentityGroups([]);
      }
    } catch (error: any) {
      console.error('Error loading labeled faces:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to load labeled faces",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectGroup = (groupId: string) => {
    const newSelection = new Set(selectedGroups);
    if (newSelection.has(groupId)) {
      newSelection.delete(groupId);
    } else {
      newSelection.add(groupId);
    }
    setSelectedGroups(newSelection);
    setSelectAll(newSelection.size === identityGroups.length);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedGroups(new Set());
      setSelectAll(false);
    } else {
      const allGroupIds = identityGroups.map(group => group.id);
      setSelectedGroups(new Set(allGroupIds));
      setSelectAll(true);
    }
  };

  const startTraining = async () => {
    if (selectedGroups.size === 0) {
      toast({
        title: "Error",
        description: "Please select at least one face group",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsTraining(true);
      // Call the backend directly instead of going through Next.js API route
      const response = await fetch('http://127.0.0.1:7860/api/training/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identity_group_ids: Array.from(selectedGroups)
        })
      });

      const data = await response.json();

      if (data.job_id) {
        setTrainingJob({
          id: data.job_id,
          status: 'queued',
          progress: 0,
          message: 'Training job queued',
          created_at: new Date().toISOString()
        });

        toast({
          title: "Training Started",
          description: "Face recognition model training has been queued",
        });

        // Start polling for job status
        pollTrainingStatus(data.job_id);
      }
    } catch (error) {
      console.error('Error starting training:', error);
      toast({
        title: "Error",
        description: "Failed to start training job",
        variant: "destructive"
      });
    } finally {
      setIsTraining(false);
    }
  };

  const pollTrainingStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://127.0.0.1:7860/api/training/status/${jobId}`);
        const status = await response.json();
        
        setTrainingJob(status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          
          if (status.status === 'completed') {
            toast({
              title: "Training Completed",
              description: "Face recognition model training completed successfully",
            });
          } else {
            toast({
              title: "Training Failed",
              description: status.message || "Training job failed",
              variant: "destructive"
            });
          }
        }
      } catch (error) {
        console.error('Error polling training status:', error);
        clearInterval(interval);
      }
    }, 5000); // Poll every 5 seconds
  };

  const getTrainingStatusIcon = () => {
    if (!trainingJob) return null;

    switch (trainingJob.status) {
      case 'queued':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    } catch (e) {
      return 'Unknown date';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Face Labeling</h2>
          <p className="text-muted-foreground">Select face groups for training</p>
        </div>
        <div className="flex items-center space-x-4">
          {trainingJob && (
            <div className="flex items-center space-x-2">
              {getTrainingStatusIcon()}
              <span className="text-sm">{trainingJob.message}</span>
              {trainingJob.status === 'processing' && (
                <Progress value={trainingJob.progress} className="w-24" />
              )}
            </div>
          )}
          <Button 
            onClick={startTraining}
            disabled={selectedGroups.size === 0 || isTraining || trainingJob?.status === 'processing'}
          >
            {isTraining ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting Training...
              </>
            ) : (
              <>
                <Brain className="mr-2 h-4 w-4" />
                Train Model ({selectedGroups.size} selected)
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Select All Checkbox */}
      <Card>
        <CardContent className="py-3">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="select-all"
              checked={selectAll}
              onCheckedChange={handleSelectAll}
            />
            <label htmlFor="select-all" className="font-medium cursor-pointer">
              Select All ({identityGroups.length} groups)
            </label>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="py-8 text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent"></div>
          <p>Loading labeled faces...</p>
        </div>
      ) : identityGroups.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <Users className="h-12 w-12 mb-4 mx-auto text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">No face groups found</h3>
            <p className="text-muted-foreground mb-4">
              Process some videos first to create face groups
            </p>
            <Button onClick={() => router.push('/facial-recognition?tab=videos')}>
              Process Videos
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {identityGroups.map((group) => (
            <Card 
              key={group.id} 
              className={`overflow-hidden cursor-pointer transition-all ${
                selectedGroups.has(group.id) ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => handleSelectGroup(group.id)}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={selectedGroups.has(group.id)}
                      onCheckedChange={() => handleSelectGroup(group.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <CardTitle className="text-lg">{group.name || group.label || `Group ${group.id}`}</CardTitle>
                  </div>
                  <Badge variant={group.name || group.employee_id ? "default" : "secondary"}>
                    {group.name || group.employee_id ?
                      <UserCheck className="h-3 w-3 mr-1" /> :
                      <UserX className="h-3 w-3 mr-1" />
                    }
                    {group.name || group.employee_id ? 'Labeled' : 'Unlabeled'}
                  </Badge>
                </div>
                <CardDescription className="flex items-center space-x-2">
                  <Calendar className="h-3 w-3" />
                  <span>{formatDate(group.created || group.created_at)}</span>
                  {group.employee_id && (
                    <>
                      <Tag className="h-3 w-3" />
                      <span>{group.employee_id}</span>
                    </>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-2">
                <div className="grid grid-cols-6 gap-1 mb-2">
                  {(group.face_ids || []).slice(0, 6).map((faceId, index) => (
                    <div key={faceId} className="relative aspect-square">
                      <img
                        src={`/static/faces/${faceId}.jpg`}
                        alt={`Face ${index + 1}`}
                        className="w-full h-full object-cover rounded"
                        onError={(e) => {
                          e.currentTarget.src = '/static/faces/placeholder.jpg';
                        }}
                      />
                    </div>
                  ))}
                </div>
                <div className="text-sm text-muted-foreground">
                  <User className="h-3 w-3 inline mr-1" />
                  {(group.face_ids || group.faces || []).length} faces
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}