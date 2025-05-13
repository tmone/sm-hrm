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
              <Image
                src={face.imageUrl}
                alt="Face"
                fill
                className="object-cover"
              />
              
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