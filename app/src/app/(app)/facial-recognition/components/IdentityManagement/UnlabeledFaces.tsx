import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import Image from 'next/image';
import { DetectedFace } from '../../types';

interface UnlabeledFacesProps {
  faces: DetectedFace[];
  isSelectionMode: boolean;
  selectedFaces: Record<string, boolean>;
  onToggleSelection: (faceId: string) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function UnlabeledFaces({
  faces,
  isSelectionMode,
  selectedFaces,
  onToggleSelection,
  currentPage,
  totalPages,
  onPageChange
}: UnlabeledFacesProps) {
  if (faces.length === 0) {
    return (
      <div className="text-center py-10 text-muted-foreground">
        No unlabeled faces found.
      </div>
    );
  }
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {faces.map(face => (
          <div 
            key={face.id} 
            className={`border rounded-md overflow-hidden relative ${
              selectedFaces[face.id] ? 'ring-2 ring-primary' : ''
            }`}
          >
            <div className="aspect-square relative">
              {/* Direct img tag instead of Next.js Image component for better reliability */}
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
              
              {isSelectionMode && (
                <div 
                  className="absolute inset-0 flex items-center justify-center bg-black/30 transition-opacity hover:bg-black/40"
                  onClick={() => onToggleSelection(face.id)}
                >
                  <Checkbox 
                    checked={selectedFaces[face.id] || false}
                    onCheckedChange={() => onToggleSelection(face.id)}
                    className="h-5 w-5 border-white"
                  />
                </div>
              )}
              
              {face.quality_score !== undefined && (
                <Badge 
                  variant="outline" 
                  className={`absolute bottom-1 right-1 text-xs ${
                    face.quality_score > 80 
                      ? 'bg-green-50 text-green-700 border-green-200' 
                      : face.quality_score > 60
                        ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                        : 'bg-red-50 text-red-700 border-red-200'
                  }`}
                >
                  Q: {face.quality_score}
                </Badge>
              )}
            </div>
            
            <div className="p-2 text-xs text-muted-foreground bg-muted/30">
              <div className="font-medium truncate">{formatTimestamp(face.timestamp)}</div>
              <div>Frame: {face.frameNumber}</div>
            </div>
          </div>
        ))}
      </div>
      
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <Button
            size="icon"
            variant="outline"
            className="h-8 w-8"
            disabled={currentPage === 1}
            onClick={() => onPageChange(currentPage - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="text-sm">
            Page {currentPage} of {totalPages}
          </span>
          
          <Button
            size="icon"
            variant="outline"
            className="h-8 w-8"
            disabled={currentPage === totalPages}
            onClick={() => onPageChange(currentPage + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}