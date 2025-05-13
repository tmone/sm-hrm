'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  FileVideo, 
  Video, 
  Clock, 
  Calendar, 
  Tag,
  Upload
} from 'lucide-react';
import { fetchFromAPI } from '../api';
import { useToast } from '@/hooks/use-toast';

// This component serves as a hub to access videos for face labeling
export default function VideoLabelingHub() {
  const router = useRouter();
  const { toast } = useToast();
  const [videos, setVideos] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      setIsLoading(true);
      const data = await fetchFromAPI('api/videos');
      
      if (data && Array.isArray(data.videos)) {
        // Sort by uploaded date (newest first)
        const sortedVideos = [...data.videos].sort((a, b) => {
          return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
        });
        setVideos(sortedVideos);
      } else {
        setVideos([]);
      }
    } catch (error) {
      console.error('Error loading videos:', error);
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

  const formatVideoName = (filename: string) => {
    // Remove extension and replace underscores/hyphens with spaces
    return filename
      .replace(/\.[^/.]+$/, "")
      .replace(/_/g, " ")
      .replace(/-/g, " ");
  };

  const goToVideoLabeling = (videoId: string) => {
    router.push(`/facial-recognition/video-labeling/${videoId}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Video Face Labeling</h2>
          <p className="text-muted-foreground">Label and organize faces detected in videos</p>
        </div>
        <Button variant="outline" onClick={() => router.push('/facial-recognition?tab=videos')}>
          <Upload className="mr-2 h-4 w-4" />
          Process New Video
        </Button>
      </div>

      {isLoading ? (
        <div className="py-8 text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent"></div>
          <p>Loading videos...</p>
        </div>
      ) : videos.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <FileVideo className="h-12 w-12 mb-4 mx-auto text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">No videos found</h3>
            <p className="text-muted-foreground mb-4">
              Upload and process a video first to start labeling faces
            </p>
            <Button onClick={() => router.push('/facial-recognition?tab=videos')}>
              Process a Video
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {videos.map((video) => (
            <Card key={video.id} className="overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg truncate">{formatVideoName(video.filename)}</CardTitle>
                <CardDescription className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3 inline" />
                  <span>{formatDate(video.uploaded_at)}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex justify-between items-center mt-2">
                  <div className="text-sm text-muted-foreground">
                    {video.processing_status === 'completed' ? (
                      <span className="text-green-600 flex items-center">
                        <Tag className="h-3 w-3 mr-1" />
                        Faces detected
                      </span>
                    ) : video.processing_status === 'processing' ? (
                      <span className="text-amber-600 flex items-center">
                        <Clock className="h-3 w-3 mr-1 animate-spin" />
                        Processing...
                      </span>
                    ) : (
                      <span className="text-muted-foreground flex items-center">
                        <Video className="h-3 w-3 mr-1" />
                        Not processed
                      </span>
                    )}
                  </div>
                  <Button 
                    onClick={() => goToVideoLabeling(video.id)}
                    disabled={video.processing_status !== 'completed'}
                  >
                    Label Faces
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}