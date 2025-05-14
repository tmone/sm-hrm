import React from 'react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Trash2 } from 'lucide-react';

export interface GroupCardProps {
  identityCode: string;
  representativeFace: {
    imageUrl: string;
    quality_score?: number;
  };
  faceCount: number;
  isSelected: boolean;
  onSelect: (groupId: string) => void;
  onViewFaces: (identityCode: string) => void;
  onDelete: (group: { identityCode: string; representativeFace: { imageUrl: string; quality_score?: number }; faceCount: number }) => void;
}

const GroupCard: React.FC<GroupCardProps> = ({
  identityCode,
  representativeFace,
  faceCount,
  isSelected,
  onSelect,
  onViewFaces,
  onDelete
}) => {
  const group = { identityCode, representativeFace, faceCount };
  
  return (
    <div 
      className={`border rounded-md overflow-hidden ${
        isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'bg-primary/5'
      } cursor-pointer hover:bg-primary/10 transition-colors relative`}
    >
      <div 
        className="absolute top-1 left-1 z-10" 
        onClick={(e) => {
          e.stopPropagation();
          onSelect(identityCode);
        }}
      >
        <Checkbox 
          checked={isSelected}
          className="h-5 w-5 bg-white/80"
        />
      </div>
      
      <div className="absolute top-1 right-1 z-10">
        <Button
          size="icon"
          variant="destructive"
          className="h-6 w-6 rounded-full bg-red-500/70 hover:bg-red-600/90"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(group);
          }}
        >
          <Trash2 className="h-3 w-3 text-white" />
        </Button>
      </div>
      
      <div 
        className="aspect-square relative cursor-pointer"
        onClick={() => onSelect(identityCode)}
      >
        {/* Direct img tag instead of Next.js Image component for better reliability */}
        <div className="relative w-full h-full">
          <img
            src={representativeFace.imageUrl}
            alt="Group Representative"
            className="absolute inset-0 w-full h-full object-cover"
            onError={(e) => {
              console.warn(`Image not found: ${representativeFace.imageUrl}`);
              
              // Extract face ID from the URL if possible
              const faceIdMatch = representativeFace.imageUrl.match(/face_id=([^&]+)/);
              const faceId = faceIdMatch ? faceIdMatch[1] : null;
              
              // Try fallback paths
              const fallbacks = [
                // Try with direct face ID path first if we have it
                faceId ? `/static/faces/${faceId}.jpg` : null,
                // Try with direct URL - no image optimization
                representativeFace.imageUrl.replace('/api/python-bridge?endpoint=face_image', '/static/faces'),
                // Try with .png extension if we have face ID
                faceId ? `/static/faces/${faceId}.png` : null,
                // Try without optimization parameters if they exist
                representativeFace.imageUrl?.split('?')[0]
              ].filter(Boolean); // Remove undefined entries
              
              // Use a recursive function to try all fallback paths
              const tryNextFallback = (index = 0) => {
                if (index >= fallbacks.length) {
                  // All fallbacks failed, show a generic face placeholder
                  console.error(`All image fallbacks failed for group representative`);
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
        
        {/* Group badge */}
        <div className="absolute inset-0 bg-black/30 flex flex-col items-center justify-center">
          <div className="text-white font-bold text-lg">{identityCode}</div>
          <div className="text-white/90 text-sm mt-1">{faceCount} faces</div>
        </div>
        
        {/* Quality indicator */}
        {representativeFace.quality_score !== undefined && (
          <Badge 
            variant="outline" 
            className="absolute bottom-1 right-1 text-xs bg-blue-500/70 text-white border-none"
          >
            Best Q: {representativeFace.quality_score}
          </Badge>
        )}
      </div>
      
      <div 
        className="p-2 text-center font-medium bg-primary/10 text-primary flex items-center justify-center px-3"
      >
        <Button 
          size="sm" 
          variant="secondary" 
          className="mr-2" 
          onClick={(e) => {
            e.stopPropagation();
            onViewFaces(identityCode);
          }}
        >
          View Faces
        </Button>
      </div>
    </div>
  );
};

export default GroupCard;