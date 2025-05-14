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
                {/* Direct img tag with enhanced error handling for better reliability */}
                <div className="relative w-full h-full">
                  <img
                    // Use face ID directly as the most reliable way to find the image
                    src={`/static/faces/${face.id}.jpg`}
                    alt="Selected face"
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