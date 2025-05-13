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
        className="aspect-square relative"
        onClick={() => onViewFaces(identityCode)}
      >
        {/* Show the representative face of the group */}
        <Image
          src={representativeFace.imageUrl}
          alt="Group Representative"
          fill
          className="object-cover"
        />
        
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
        className="p-2 text-center font-medium bg-primary/10 text-primary flex items-center justify-between px-3"
        onClick={() => onSelect(identityCode)}
      >
        <div>Select</div>
        <div onClick={(e) => {
          e.stopPropagation();
          onViewFaces(identityCode);
        }}>View Faces</div>
      </div>
    </div>
  );
};

export default GroupCard;