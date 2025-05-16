'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  User, 
  Calendar, 
  Tag,
  UserCheck,
  UserX,
  FolderOpen
} from 'lucide-react';
import { fetchFromAPI } from '../api';
import { useToast } from '@/hooks/use-toast';

// This component serves as a hub to display face groups for batch labeling
export default function FaceGroupsHub() {
  const router = useRouter();
  const { toast } = useToast();
  const [groups, setGroups] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadFaceGroups();
  }, []);

  const loadFaceGroups = async () => {
    try {
      setIsLoading(true);
      const data = await fetchFromAPI('api/face-groups');
      
      if (data && data.groups) {
        // Sort by created date (newest first)
        const sortedGroups = [...data.groups].sort((a, b) => {
          return new Date(b.created).getTime() - new Date(a.created).getTime();
        });
        setGroups(sortedGroups);
      } else {
        setGroups([]);
      }
    } catch (error) {
      console.error('Error loading face groups:', error);
      // No toast notification for failed data load
    } finally {
      setIsLoading(false);
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

  const getGroupStatusIcon = (group: any) => {
    if (group.labeled) {
      return <UserCheck className="h-4 w-4 text-green-600" />;
    } else {
      return <UserX className="h-4 w-4 text-amber-600" />;
    }
  };

  const getGroupStatusText = (group: any) => {
    if (group.labeled) {
      return 'Labeled';
    } else {
      return 'Unlabeled';
    }
  };

  const getGroupBadgeVariant = (group: any): "default" | "secondary" | "destructive" | "outline" => {
    if (group.labeled) {
      return "default";
    } else {
      return "secondary";
    }
  };

  const handleGroupClick = (groupId: string) => {
    // Navigate to a group detail/labeling page
    router.push(`/facial-recognition/face-groups/${groupId}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Face Groups</h2>
          <p className="text-muted-foreground">Manage and label grouped faces</p>
        </div>
        <Button variant="outline" onClick={() => router.push('/facial-recognition?tab=videos')}>
          <FolderOpen className="mr-2 h-4 w-4" />
          Process Videos
        </Button>
      </div>

      {isLoading ? (
        <div className="py-8 text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent"></div>
          <p>Loading face groups...</p>
        </div>
      ) : groups.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <Users className="h-12 w-12 mb-4 mx-auto text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">No face groups found</h3>
            <p className="text-muted-foreground mb-4">
              Process videos to create face groups for batch labeling
            </p>
            <Button onClick={() => router.push('/facial-recognition?tab=videos')}>
              Process Videos
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map((group) => (
            <Card 
              key={group.id} 
              className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleGroupClick(group.id)}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">
                    {group.label || `Group ${group.id.substring(0, 8)}...`}
                  </CardTitle>
                  <Badge variant={getGroupBadgeVariant(group)}>
                    {getGroupStatusIcon(group)}
                    <span className="ml-1">{getGroupStatusText(group)}</span>
                  </Badge>
                </div>
                <CardDescription className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3 inline" />
                  <span>{formatDate(group.created)}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex justify-between items-center mt-2">
                  <div className="text-sm text-muted-foreground flex items-center">
                    <User className="h-3 w-3 mr-1" />
                    <span>{group.face_ids.length} faces</span>
                  </div>
                  {group.similarity_score > 0 && (
                    <div className="text-sm text-muted-foreground">
                      Match: {(group.similarity_score * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
                {group.employee_id && (
                  <div className="mt-2 text-sm">
                    <span className="font-medium">Employee:</span> {group.employee_id}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}