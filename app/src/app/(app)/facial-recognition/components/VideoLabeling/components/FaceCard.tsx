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
}

const FaceCard: React.FC<FaceCardProps> = ({
  face,
  isSelected,
  onSelect,
  onDelete,
  recentlyRemovedFaceId,
  formatTimestamp
}) => {
  return (
    <div 
      key={face.id} 
      className={`border rounded-md overflow-hidden relative ${
        isSelected ? 'ring-2 ring-primary' : ''
      } ${
        recentlyRemovedFaceId === face.id ? 'ring-2 ring-blue-500 animate-pulse' : ''
      }`}
    >
      {recentlyRemovedFaceId === face.id && (
        <div className="absolute inset-0 bg-blue-500/10 z-10 flex items-center justify-center pointer-events-none">
          <Badge className="bg-blue-500 text-white pointer-events-none">
            Removed from group
          </Badge>
        </div>
      )}
      <div className="aspect-square relative">
        <Image
          src={face.imageUrl}
          alt="Face"
          fill
          className="object-cover"
        />
        
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
      </div>
      
      <div className="p-2 text-xs font-medium bg-muted/30">
        {formatTimestamp(face.timestamp)}
      </div>
    </div>
  );
};

export default FaceCard;