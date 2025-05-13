import React from 'react';
import Image from 'next/image';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { CheckCheck } from 'lucide-react';
import { DetectedFace } from '../../../types';

export interface GroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedFaces: Record<string, boolean>;
  faces: DetectedFace[];
  onGroupFaces: () => Promise<void>;
}

const GroupDialog: React.FC<GroupDialogProps> = ({
  open,
  onOpenChange,
  selectedFaces,
  faces,
  onGroupFaces
}) => {
  // Get selected faces
  const selectedFacesList = faces.filter(face => selectedFaces[face.id]);
  const selectedFaceCount = selectedFacesList.length;
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Identity Group</DialogTitle>
          <DialogDescription>
            You are about to group {selectedFaceCount} face{selectedFaceCount !== 1 ? 's' : ''} into a single identity.
            This will assign {selectedFaceCount === 1 ? 'it' : 'them all'} the same PERSON-XXXX identifier.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <h4 className="font-medium mb-2">Selected Faces:</h4>
          <div className="grid grid-cols-4 gap-2 max-h-60 overflow-y-auto p-2 border rounded-md">
            {selectedFacesList.map(face => (
              <div key={face.id} className="relative h-20 rounded-md overflow-hidden">
                <Image
                  src={face.imageUrl}
                  alt="Selected face"
                  fill
                  className="object-cover"
                />
              </div>
            ))}
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onGroupFaces}>
            <CheckCheck className="mr-2 h-4 w-4" />
            Confirm Grouping
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default GroupDialog;