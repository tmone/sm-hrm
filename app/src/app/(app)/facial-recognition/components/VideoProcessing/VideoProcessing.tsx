import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { Video, Upload, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { UploadedVideo, ProcessingTask, APIError, NetworkError, ValidationError } from '../../types';
import { fetchVideos, uploadVideo, processVideo, fetchTaskStatus, deleteVideo } from '../../api';
import VideoList from './VideoList';
import UploadForm from './UploadForm';
import ClientOnly from '@/components/client-only';

export default function VideoProcessing() {
  const { toast } = useToast();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingError, setIsLoadingError] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [uploadedVideos, setUploadedVideos] = useState<UploadedVideo[]>([]);
  const [processingTasks, setProcessingTasks] = useState<Record<string, ProcessingTask>>({});
  const [pollingTasks, setPollingTasks] = useState<string[]>([]);

  // Fetch videos on component mount
  useEffect(() => {
    loadVideos();
  }, []);

  // Poll for task status updates
  useEffect(() => {
    // Set up polling for tasks that are in progress
    const interval = setInterval(() => {
      if (pollingTasks.length > 0) {
        pollingTasks.forEach(taskId => {
          updateTaskStatus(taskId);
        });
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [pollingTasks]);

  const loadVideos = async (isRefreshOperation = false) => {
    try {
      if (isRefreshOperation) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setIsLoadingError(false);
      
      const videos = await fetchVideos();
      setUploadedVideos(videos);
      
      // Check for videos with active tasks
      videos.forEach(video => {
        if (video.task_id && 
            (video.processing_status === 'processing' || 
             video.processing_status === 'pending')) {
          // Add task to polling list
          setPollingTasks(prev => {
            if (!prev.includes(video.task_id!)) {
              return [...prev, video.task_id!];
            }
            return prev;
          });
          
          // Get initial task status
          updateTaskStatus(video.task_id);
        }
      });

      if (isRefreshOperation) {
        toast({
          title: 'Videos refreshed',
          description: 'The video list has been updated successfully',
        });
      }
    } catch (error) {
      console.error('Error loading videos:', error);
      setIsLoadingError(true);
      
      // No toast notification for failed data load
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const updateTaskStatus = async (taskId: string) => {
    try {
      const taskStatus = await fetchTaskStatus(taskId);
      
      // Handle case where taskStatus might be null
      if (!taskStatus) {
        console.error(`Received null task status for task ${taskId}`);
        // Don't remove from polling - might be a temporary issue
        // Just skip this update and try again later
        return;
      }
      
      // Store task status in state
      setProcessingTasks(prev => ({
        ...prev,
        [taskId]: taskStatus
      }));
      
      // Special handling for progress = -1, which indicates an uncertain status
      // due to network or server errors
      const isUncertainStatus = taskStatus.progress === -1;
      
      // Update video status based on task
      setUploadedVideos(prev => {
        return prev.map(video => {
          if (video.task_id === taskId) {
            // For uncertain status, keep the UI state as processing
            // but don't update the backend status
            if (isUncertainStatus) {
              return {
                ...video,
                // Keep existing processing_status
                ui_processing: true // Force UI to show as processing
              };
            }
            
            return {
              ...video,
              processing_status: taskStatus.status,
              ui_processing: taskStatus.status === 'processing' || taskStatus.status === 'pending'
            };
          }
          return video;
        });
      });
      
      // Only remove completed tasks from polling
      // For failed tasks, keep polling for a while in case the backend recovers
      if (taskStatus.status === 'completed') {
        setPollingTasks(prev => prev.filter(id => id !== taskId));
      } else if (taskStatus.status === 'failed') {
        // For failed tasks, we'll keep polling for an additional 5 minutes (150 attempts at 2-second intervals)
        // This gives the backend time to recover if it's just a temporary issue
        
        // Get current retry count from state or initialize it
        const currentAttempt = taskStatus.retry_count || 0;
        const MAX_RETRIES = 150; // 5 minutes of 2-second polling
        
        if (currentAttempt >= MAX_RETRIES) {
          // Give up after max retries
          setPollingTasks(prev => prev.filter(id => id !== taskId));
          
          // Update UI to show definitely failed
          setUploadedVideos(prev => {
            return prev.map(video => {
              if (video.task_id === taskId) {
                return {
                  ...video,
                  processing_status: 'failed',
                  ui_processing: false
                };
              }
              return video;
            });
          });
        } else {
          // Increment retry count
          setProcessingTasks(prev => ({
            ...prev,
            [taskId]: {
              ...taskStatus,
              retry_count: currentAttempt + 1
            }
          }));
          
          // Keep in polling list
          // The retry logic allows failed tasks to keep being polled
          // in case the backend recovers
        }
      }
    } catch (error) {
      console.error(`Error updating task status for ${taskId}:`, error);
      
      // For any errors in this function itself, we don't want to remove the task from polling immediately
      // Instead, we'll track retry attempts
      
      // Get the task from state
      const currentTask = processingTasks[taskId];
      const currentAttempt = currentTask?.update_retry_count || 0;
      const MAX_UPDATE_RETRIES = 10; // More reasonable limit for this function's errors
      
      if (currentAttempt >= MAX_UPDATE_RETRIES) {
        // Remove from polling after max retries
        setPollingTasks(prev => prev.filter(id => id !== taskId));
      } else {
        // Increment retry count
        setProcessingTasks(prev => ({
          ...prev,
          [taskId]: {
            ...(prev[taskId] || { 
              task_id: taskId, 
              video_id: '', 
              status: 'processing' 
            }),
            update_retry_count: currentAttempt + 1
          }
        }));
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setVideoFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!videoFile) {
      toast({
        title: 'No file selected',
        description: 'Please select a video file to upload',
        variant: 'destructive'
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const response = await uploadVideo(videoFile, (progress) => {
        setUploadProgress(progress);
      });

      setUploadedVideos(prev => [response, ...prev]);
      
      toast({
        title: 'Video uploaded successfully',
        description: 'Your video has been uploaded and is ready for processing',
      });
      
      setIsDialogOpen(false);
      setVideoFile(null);
    } catch (error) {
      console.error('Upload error:', error);
      
      // Provide more specific error messages based on error type
      if (error instanceof ValidationError && error.message.includes('File size exceeds')) {
        toast({
          title: 'File too large',
          description: error.message + '. Try compressing your video or splitting it into smaller segments.',
          variant: 'destructive'
        });
      } else {
        toast({
          title: 'Upload failed',
          description: 'There was an error uploading your video. Please try again.',
          variant: 'destructive'
        });
      }
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Helper to check if a video is already being processed
  const isVideoCurrentlyProcessing = (videoId: string): boolean => {
    // Check if video exists in uploadedVideos and is marked as processing
    const video = uploadedVideos.find(v => v.id === videoId);
    if (!video) return false;
    
    // First check UI status
    if (video.ui_processing) return true;
    
    // Then check processing status
    if (video.processing_status === 'processing' || video.processing_status === 'pending') return true;
    
    // Then check if it has a task_id that's in the polling tasks
    if (video.task_id && pollingTasks.includes(video.task_id)) return true;
    
    // Otherwise, it's not being processed
    return false;
  };

  const handleProcessVideo = async (videoId: string) => {
    try {
      // Safety check to prevent double processing
      if (isVideoCurrentlyProcessing(videoId)) {
        console.warn(`Attempted to process video ${videoId} which is already processing.`);
        toast({
          title: 'Already processing',
          description: 'This video is already being processed. Please wait for it to complete.',
          variant: 'default'
        });
        return;
      }
      
      // Update UI state first to prevent duplicate clicks
      setUploadedVideos(prev => {
        return prev.map(video => {
          if (video.id === videoId) {
            return { 
              ...video, 
              ui_processing: true,
              processing_status: 'pending' // Set to pending until we get a task
            };
          }
          return video;
        });
      });
      
      // Process the video
      const task = await processVideo(videoId);
      
      // Validate task response
      if (!task || !task.task_id) {
        throw new Error('Invalid task response from server');
      }
      
      // Add task to processingTasks
      setProcessingTasks(prev => ({
        ...prev,
        [task.task_id]: {
          ...task,
          last_updated: new Date().toISOString(), // Add timestamp for tracking
          retry_count: 0,
          update_retry_count: 0
        }
      }));
      
      // Add task to polling
      setPollingTasks(prev => {
        // Prevent duplicate task IDs
        if (prev.includes(task.task_id)) {
          return prev;
        }
        return [...prev, task.task_id];
      });
      
      // Update video with task info
      setUploadedVideos(prev => {
        return prev.map(video => {
          if (video.id === videoId) {
            return {
              ...video,
              task_id: task.task_id,
              processing_status: task.status || 'processing',
              ui_processing: true
            };
          }
          return video;
        });
      });
      
      toast({
        title: 'Processing started',
        description: 'The video is now being processed to detect faces',
      });
    } catch (error) {
      console.error('Processing error:', error);
      
      // Reset UI state
      setUploadedVideos(prev => {
        return prev.map(video => {
          if (video.id === videoId) {
            return { 
              ...video, 
              ui_processing: false,
              // Keep existing processing_status if it was already failed
              processing_status: video.processing_status === 'failed' 
                ? 'failed' 
                : 'not_processed'
            };
          }
          return video;
        });
      });
      
      toast({
        title: 'Processing failed',
        description: 'There was an error starting the processing task. Please try again.',
        variant: 'destructive'
      });
    }
  };
  
  const handleDeleteVideo = async (videoId: string) => {
    setVideoToDelete(videoId);
    setIsDeleteDialogOpen(true);
  };
  
  const confirmDeleteVideo = async () => {
    if (!videoToDelete) return;
    
    setIsDeleting(true);
    
    try {
      await deleteVideo(videoToDelete);
      
      // Remove video from state
      setUploadedVideos(prev => prev.filter(video => video.id !== videoToDelete));
      
      toast({
        title: 'Video deleted',
        description: 'The video has been deleted successfully',
      });
      
    } catch (error) {
      console.error('Error deleting video:', error);
      toast({
        title: 'Deletion failed',
        description: 'There was an error deleting the video. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setIsDeleting(false);
      setVideoToDelete(null);
      setIsDeleteDialogOpen(false);
    }
  };

  // Function to handle manual refresh
  const handleRefresh = () => {
    loadVideos(true);
  };
  
  // Render loading skeleton
  const renderLoadingSkeleton = () => {
    return (
      <div className="space-y-4 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center space-x-4 border-b pb-4">
            <Skeleton className="h-12 w-12 rounded-md" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
            <div className="flex space-x-2">
              <Skeleton className="h-8 w-20 rounded-md" />
              <Skeleton className="h-8 w-20 rounded-md" />
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  // Render error state
  const renderErrorState = () => {
    return (
      <div className="text-center p-8">
        <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-medium mb-2">No data</h3>
        <p className="text-muted-foreground mb-4">
          Please try again or upload a new video.
        </p>
        <Button 
          variant="outline" 
          onClick={handleRefresh}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Try Again
        </Button>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Video Management</h2>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={handleRefresh} 
            disabled={isLoading || isRefreshing}
            className="gap-2"
          >
            {isRefreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Refresh
          </Button>
          <Button 
            onClick={() => setIsDialogOpen(true)}
            className="gap-2"
          >
            <Upload className="h-4 w-4" />
            Upload Video
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Uploaded Videos</span>
            {isLoading && !isLoadingError && (
              <span className="text-sm font-normal text-muted-foreground flex items-center">
                <Loader2 className="h-3 w-3 animate-spin mr-2" />
                Loading...
              </span>
            )}
          </CardTitle>
          <CardDescription>Videos uploaded for face detection and recognition</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && !isRefreshing && !isLoadingError ? (
            renderLoadingSkeleton()
          ) : isLoadingError ? (
            renderErrorState()
          ) : (
            <VideoList
              videos={uploadedVideos}
              tasks={processingTasks}
              onProcess={handleProcessVideo}
              onDelete={handleDeleteVideo}
              isRefreshing={isRefreshing}
            />
          )}
        </CardContent>
      </Card>

      <ClientOnly>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[550px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Upload Video</DialogTitle>
              <DialogDescription>
                Upload a video file to detect and recognize faces.
              </DialogDescription>
            </DialogHeader>
            
            <div className="overflow-hidden">
              <UploadForm
                videoFile={videoFile}
                isUploading={isUploading}
                uploadProgress={uploadProgress}
                onFileChange={handleFileChange}
              />
            </div>

            <DialogFooter className="flex-wrap gap-2 sm:justify-end">
              <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isUploading}>
                Cancel
              </Button>
              <Button 
                onClick={handleUpload} 
                disabled={!videoFile || isUploading}
                className="gap-2"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Upload
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        
        <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Video</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this video? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
              <AlertDialogAction 
                onClick={confirmDeleteVideo}
                disabled={isDeleting}
                className="bg-red-600 hover:bg-red-700"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </ClientOnly>
    </div>
  );
}