import React from 'react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Trash2 } from 'lucide-react';
import { DetectedFace } from '../../../types';

export interface FaceCardProps {
  face: DetectedFace;
  isSelected: boolean;
  onSelect: (faceId: string) => void;
  onDelete: (face: DetectedFace) => void;
  recentlyRemovedFaceId: string | null;
  formatTimestamp: (timestamp: string) => string;
  missingFile?: boolean;
  onImageLoadError?: (faceId: string) => void;
}

const FaceCard: React.FC<FaceCardProps> = ({
  face,
  isSelected,
  onSelect,
  onDelete,
  recentlyRemovedFaceId,
  formatTimestamp,
  missingFile = false,
  onImageLoadError
}) => {
  return (
    <div 
      key={face.id} 
      className={`border rounded-md overflow-hidden relative ${
        isSelected ? 'ring-2 ring-primary' : ''
      } ${
        recentlyRemovedFaceId === face.id ? 'ring-2 ring-blue-500 animate-pulse' : ''
      } ${
        missingFile ? 'ring-2 ring-red-500' : ''
      }`}
    >
      {recentlyRemovedFaceId === face.id && (
        <div className="absolute inset-0 bg-blue-500/10 z-10 flex items-center justify-center pointer-events-none">
          <Badge className="bg-blue-500 text-white pointer-events-none">
            Removed from group
          </Badge>
        </div>
      )}
      <div className="aspect-square relative cursor-pointer" onClick={() => onSelect(face.id)}>
        {/* Direct img tag with enhanced error handling for better reliability */}
        <div className="relative w-full h-full">
          <img
            // Use face ID directly as the most reliable way to find the image
            src={`/static/faces/${face.id}.jpg`}
            alt="Face"
            className="absolute inset-0 w-full h-full object-cover"
            onError={(e) => {
              console.warn(`Image not found: /static/faces/${face.id}.jpg`);
              
              // Try fallback paths
              const fallbacks = [
                // Try with imageUrl from the face object
                face.imageUrl,
                // Try with .png extension
                `/static/faces/${face.id}.png`,
                // Try without optimization parameters if they exist
                face.imageUrl?.split('?')[0],
                // Try with imageUrl field (some records use this instead)
                face.image_url
              ].filter(Boolean); // Remove undefined entries
              
              // Use a recursive function to try all fallback paths
              const tryNextFallback = (index = 0) => {
                if (index >= fallbacks.length) {
                  // All fallbacks failed, show a generic face placeholder
                  console.error(`All image fallbacks failed for face ${face.id}`);
                  
                  // Call the image load error callback if provided
                  if (onImageLoadError) {
                    onImageLoadError(face.id);
                  }
                  
                  // Just hide the image with CSS rather than using a placeholder
                  // @ts-ignore - We'll just make the image invisible
                  e.currentTarget.style.display = 'none';
                  return;
                }
                
                const nextSrc = fallbacks[index];
                // @ts-ignore - Update the src attribute
                e.currentTarget.src = nextSrc;
                
                // Add onError handler to try the next fallback
                // @ts-ignore
                e.currentTarget.onerror = () => {
                  tryNextFallback(index + 1);
                };
              };
              
              tryNextFallback();
            }}
          />
        </div>
        
        <div className="absolute top-1 left-1 z-10">
          <Checkbox 
            checked={isSelected}
            className="h-5 w-5 bg-white/80"
            onClick={(e) => e.stopPropagation()}
            onCheckedChange={() => onSelect(face.id)}
          />
        </div>
        <div className="absolute top-1 right-1">
          <Button
            size="icon"
            variant="destructive"
            className="h-6 w-6 rounded-full bg-red-500/70 hover:bg-red-600/90"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(face);
            }}
          >
            <Trash2 className="h-3 w-3 text-white" />
          </Button>
        </div>
        
        {face.identity_code && (
          <Badge 
            variant="outline" 
            className="absolute bottom-1 left-1 bg-black/50 text-white border-none"
          >
            {face.identity_code}
          </Badge>
        )}
        
        {face.quality_score !== undefined && (
          <Badge 
            variant="outline" 
            className={`absolute bottom-1 right-1 text-xs ${
              face.quality_score > 80 
                ? 'bg-green-500/70 text-white border-none' 
                : face.quality_score > 60
                  ? 'bg-yellow-500/70 text-white border-none'
                  : 'bg-red-500/70 text-white border-none'
            }`}
          >
            Q: {face.quality_score}
          </Badge>
        )}
        
        {missingFile && (
          <Badge
            variant="outline"
            className="absolute top-1 left-1/2 transform -translate-x-1/2 bg-red-500/90 text-white border-none z-20"
          >
            Missing File
          </Badge>
        )}
      </div>
      
      <div className="p-2 text-xs font-medium bg-muted/30 flex justify-between items-center">
        <span>{formatTimestamp(face.timestamp)}</span>
        {face.frameNumber && <span>Frame: {face.frameNumber}</span>}
      </div>
    </div>
  );
};

export default FaceCard;