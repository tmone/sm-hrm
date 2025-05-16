'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  ArrowLeft,
  Users,
  Calendar,
  UserCheck,
  UserX,
  Tag
} from 'lucide-react';
import { fetchFromAPI } from '../../api';
import { useToast } from '@/hooks/use-toast';

interface FaceGroupDetail {
  id: string;
  face_ids: string[];
  similarity_score: number;
  created: string;
  last_updated: string;
  labeled: boolean;
  label: string | null;
  employee_id: string | null;
}

export default function FaceGroupDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const groupId = params.groupId as string;
  
  const [group, setGroup] = useState<FaceGroupDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [employeeId, setEmployeeId] = useState('');
  const [label, setLabel] = useState('');

  useEffect(() => {
    if (groupId) {
      loadGroupDetails();
    }
  }, [groupId]);

  const loadGroupDetails = async () => {
    try {
      setIsLoading(true);
      const data = await fetchFromAPI(`api/face-groups/${groupId}`);
      setGroup(data);
      
      // Set initial form values
      if (data.employee_id) {
        setEmployeeId(data.employee_id);
      }
      if (data.label) {
        setLabel(data.label);
      }
    } catch (error) {
      console.error('Error loading group details:', error);
      toast({
        title: "Error",
        description: "Failed to load group details",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLabelGroup = async () => {
    if (!employeeId || !label) {
      toast({
        title: "Error",
        description: "Please enter both employee ID and label",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsSaving(true);
      await fetchFromAPI(`api/face-groups/${groupId}/label`, {
        method: 'POST',
        body: JSON.stringify({
          employee_id: employeeId,
          label: label
        })
      });

      toast({
        title: "Success",
        description: "Face group labeled successfully"
      });

      // Reload group details
      await loadGroupDetails();
    } catch (error) {
      console.error('Error labeling group:', error);
      toast({
        title: "Error",
        description: "Failed to label group",
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="py-8 text-center">
        <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent"></div>
        <p>Loading group details...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="py-8 text-center">
        <h3 className="text-lg font-medium mb-2">Group not found</h3>
        <Button onClick={() => router.push('/facial-recognition?tab=labeling')}>
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button 
          variant="outline" 
          onClick={() => router.push('/facial-recognition?tab=labeling')}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Groups
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Face Group Details</CardTitle>
              <CardDescription>
                {group.label || `Group ${group.id.substring(0, 8)}...`}
              </CardDescription>
            </div>
            <Badge variant={group.labeled ? "default" : "secondary"}>
              {group.labeled ? <UserCheck className="h-4 w-4 mr-1" /> : <UserX className="h-4 w-4 mr-1" />}
              {group.labeled ? 'Labeled' : 'Unlabeled'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium">{new Date(group.created).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Updated</p>
              <p className="font-medium">{new Date(group.last_updated).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Faces</p>
              <p className="font-medium">{group.face_ids.length}</p>
            </div>
            {group.similarity_score > 0 && (
              <div>
                <p className="text-sm text-muted-foreground">Similarity</p>
                <p className="font-medium">{(group.similarity_score * 100).toFixed(0)}%</p>
              </div>
            )}
          </div>

          <div className="pt-4 border-t">
            <h3 className="text-lg font-semibold mb-4">Label Face Group</h3>
            <div className="grid gap-4">
              <div>
                <Label htmlFor="employee-id">Employee ID</Label>
                <Input
                  id="employee-id"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  placeholder="Enter employee ID"
                  disabled={group.labeled}
                />
              </div>
              <div>
                <Label htmlFor="label">Label</Label>
                <Input
                  id="label"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="Enter label (e.g., employee name)"
                  disabled={group.labeled}
                />
              </div>
              <Button 
                onClick={handleLabelGroup}
                disabled={group.labeled || isSaving}
                className="w-full"
              >
                {isSaving ? "Saving..." : (group.labeled ? "Already Labeled" : "Label Group")}
              </Button>
            </div>
          </div>

          {group.labeled && (
            <div className="pt-4 border-t">
              <h3 className="text-lg font-semibold mb-2">Current Label</h3>
              <div className="space-y-2">
                <p><strong>Employee ID:</strong> {group.employee_id}</p>
                <p><strong>Label:</strong> {group.label}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Face Images</CardTitle>
          <CardDescription>All faces in this group</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {group.face_ids.map((faceId) => (
              <div key={faceId} className="relative aspect-square">
                <img
                  src={`/static/faces/${faceId}`}
                  alt={`Face ${faceId}`}
                  className="w-full h-full object-cover rounded-lg"
                  onError={(e) => {
                    e.currentTarget.src = '/static/faces/placeholder.jpg';
                  }}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}