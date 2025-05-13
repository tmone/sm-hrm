import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Label } from '@/components/ui/label';
import { UploadCloud, Video } from 'lucide-react';

interface UploadFormProps {
  videoFile: File | null;
  isUploading: boolean;
  uploadProgress: number;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export default function UploadForm({ 
  videoFile, 
  isUploading, 
  uploadProgress, 
  onFileChange 
}: UploadFormProps) {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="grid gap-4 py-4" onSubmit={(e) => e.preventDefault()}>
      <div className="grid gap-2">
        <Label htmlFor="video-file">Video File</Label>
        <input
          ref={fileInputRef}
          type="file"
          id="video-file"
          accept="video/*"
          onChange={onFileChange}
          className="hidden"
          disabled={isUploading}
        />
        
        {!videoFile ? (
          <div 
            onClick={handleClick}
            className="flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg h-44 cursor-pointer hover:bg-muted/50 transition-colors"
          >
            <div className="text-center">
              <UploadCloud className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 font-medium">Click to upload a video</p>
              <p className="text-xs text-muted-foreground mt-1">
                MP4, MOV, or AVI. Max 500MB.
              </p>
            </div>
          </div>
        ) : (
          <div className="border rounded-lg p-4 bg-muted/20">
            <div className="flex items-start gap-3">
              <div className="w-12 h-8 rounded bg-muted flex items-center justify-center">
                <Video className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0"> {/* Added min-width to ensure proper truncation */}
                <div className="max-w-full overflow-hidden">
                  <p className="font-medium truncate" title={videoFile.name}>{videoFile.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(videoFile.size)}
                  </p>
                </div>
                
                {isUploading && (
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-1" />
                  </div>
                )}
              </div>
            </div>
            
            {!isUploading && (
              <button
                onClick={handleClick}
                className="mt-3 text-xs text-primary hover:underline"
                disabled={isUploading}
              >
                Change file
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}