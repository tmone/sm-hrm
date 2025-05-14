import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Video, AlertCircle, Loader2, CheckCircle, RefreshCw, Trash2, Users, Tag } from 'lucide-react';
import { UploadedVideo, ProcessingTask } from '../../types';
import { formatDate } from '../../utils';

interface VideoListProps {
  videos: UploadedVideo[];
  tasks: Record<string, ProcessingTask>;
  onProcess: (videoId: string) => void;
  onDelete: (videoId: string) => void;
  isRefreshing?: boolean;
}

export default function VideoList({ videos, tasks, onProcess, onDelete, isRefreshing = false }: VideoListProps) {
  const router = useRouter();
  const renderStatus = (video: UploadedVideo) => {
    const task = video.task_id ? tasks[video.task_id] : null;
    
    // Handle cases where UI indicates processing
    if (video.ui_processing || 
        video.processing_status === 'processing' || 
        video.processing_status === 'pending') {
      
      const progress = task?.progress || 0;
      
      // Special handling for uncertain progress (-1)
      // This is set by our fetchTaskStatus function when network errors occur
      if (progress === -1) {
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span className="text-blue-600 font-medium">
                Checking status...
              </span>
            </div>
            <Progress value={50} className="h-2 w-full animate-pulse" />
            <div className="text-xs text-muted-foreground">
              Connection issues - retrying
            </div>
          </div>
        );
      }
      
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
            <span className="text-blue-600 font-medium">Processing...</span>
          </div>
          <Progress value={progress} className="h-2 w-full" />
          {task?.face_count !== undefined && (
            <div className="text-xs text-muted-foreground">
              Detected {task.face_count} faces
            </div>
          )}
        </div>
      );
    }
    
    // Handle completed status
    if (video.processing_status === 'completed') {
      const faceCount = task?.face_count || 0;
      return (
        <div className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <span className="text-green-600 font-medium">
            Completed ({faceCount} faces)
          </span>
        </div>
      );
    }
    
    // Handle failed status - check if we're still retrying
    if (video.processing_status === 'failed') {
      // If the task has a retry count and it's still being polled, show retrying
      if (task?.retry_count !== undefined && task.retry_count < 150) {
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-orange-500" />
              <span className="text-orange-500 font-medium">
                Reconnecting...
              </span>
            </div>
            <Progress value={30} className="h-2 w-full bg-orange-100" />
            <div className="text-xs text-muted-foreground">
              Connection lost - retrying ({task.retry_count}/150)
            </div>
          </div>
        );
      }
      
      // Regular failed state after retries are exhausted
      return (
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <span className="text-red-600 font-medium">
            Failed
          </span>
          {task?.error && (
            <div className="text-xs text-red-400 mt-1">
              {task.error.length > 50 ? task.error.substring(0, 50) + '...' : task.error}
            </div>
          )}
        </div>
      );
    }
    
    // Default: Not processed
    return (
      <Badge variant="outline">Not Processed</Badge>
    );
  };

  return (
    <div className={`rounded-md border ${isRefreshing ? 'opacity-60' : ''}`}>
      <div className="relative w-full overflow-auto">
        {isRefreshing && (
          <div className="absolute inset-0 bg-background/50 flex items-center justify-center z-10">
            <div className="flex items-center gap-2 bg-background px-4 py-2 rounded-md shadow-sm">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm font-medium">Refreshing...</span>
            </div>
          </div>
        )}
        <table className="w-full caption-bottom text-sm table-fixed">
          <thead className="[&_tr]:border-b">
            <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-[30%]">Video</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-[20%]">Upload Date</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-[25%]">Status</th>
              <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-[25%]">Actions</th>
            </tr>
          </thead>
          <tbody className="[&_tr:last-child]:border-0">
            {videos.length === 0 ? (
              <tr key="no-videos">
                <td colSpan={4} className="h-24 text-center text-muted-foreground">
                  No videos have been uploaded yet.
                </td>
              </tr>
            ) : (
              videos.map((video) => (
                <tr 
                  key={video.id} 
                  className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                >
                  <td className="p-4 align-middle">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-8 rounded bg-muted flex items-center justify-center flex-shrink-0">
                        <Video className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="min-w-0 max-w-[200px]">
                        <div className="font-medium truncate" title={video.filename}>{video.filename}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 align-middle">
                    {formatDate(video.uploaded_at)}
                  </td>
                  <td className="p-4 align-middle">
                    {renderStatus(video)}
                  </td>
                  <td className="p-4 align-middle">
                    <div className="flex items-center gap-2">
                      {/* Process Button - improved locking mechanism */}
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 gap-1"
                        onClick={() => onProcess(video.id)}
                        disabled={
                          // Disable if any of these conditions are true:
                          video.ui_processing ||
                          video.processing_status === 'processing' || 
                          video.processing_status === 'pending' ||
                          video.processing_status === 'completed' || 
                          isRefreshing
                        }
                      >
                        {video.ui_processing || 
                         video.processing_status === 'processing' || 
                         video.processing_status === 'pending' ? (
                          <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="h-3.5 w-3.5" />
                            {video.processing_status === 'completed' ? 'Processed' : 'Process'}
                          </>
                        )}
                      </Button>
                      
                      {video.processing_status === 'completed' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1"
                          onClick={() => router.push(`/facial-recognition/video-labeling/${video.id}`)}
                          disabled={isRefreshing}
                        >
                          <Tag className="h-3.5 w-3.5" />
                          Label Faces
                        </Button>
                      )}
                      
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="h-8 gap-1 text-red-600"
                        onClick={() => onDelete(video.id)}
                        disabled={isRefreshing}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}