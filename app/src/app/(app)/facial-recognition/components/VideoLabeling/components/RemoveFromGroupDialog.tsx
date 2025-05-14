import React from 'react';
import Image from 'next/image';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '@/components/ui/alert-dialog';
import { DetectedFace } from '../../../types';

export interface RemoveFromGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  faceToRemove: DetectedFace | null;
  isRemoving: boolean;
  onRemove: () => Promise<void>;
}

const RemoveFromGroupDialog: React.FC<RemoveFromGroupDialogProps> = ({
  open,
  onOpenChange,
  faceToRemove,
  isRemoving,
  onRemove
}) => {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remove Face from Group</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to remove this face from its group? The face will be kept as an individual face.
          </AlertDialogDescription>
          {faceToRemove?.identity_code && (
            <div className="mt-2 text-blue-600 font-medium text-sm">
              This face will be removed from identity group <span className="font-bold">{faceToRemove.identity_code}</span>.
            </div>
          )}
        </AlertDialogHeader>
        
        {faceToRemove && (
          <div className="py-4 flex justify-center">
            <div className="w-40 h-40 relative rounded overflow-hidden">
              {/* Direct img tag with enhanced error handling for better reliability */}
              <div className="relative w-full h-full">
                <img
                  // Use face ID directly as the most reliable way to find the image
                  src={`/static/faces/${faceToRemove.id}.jpg`}
                  alt="Face to remove from group"
                  className="absolute inset-0 w-full h-full object-cover"
                  onError={(e) => {
                    console.warn(`Image not found: /static/faces/${faceToRemove.id}.jpg`);
                    
                    // Try fallback paths
                    const fallbacks = [
                      // Try with imageUrl from the face object
                      faceToRemove.imageUrl,
                      // Try with .png extension
                      `/static/faces/${faceToRemove.id}.png`,
                      // Try without optimization parameters if they exist
                      faceToRemove.imageUrl?.split('?')[0],
                      // Try with imageUrl field (some records use this instead)
                      faceToRemove.image_url
                    ].filter(Boolean); // Remove undefined entries
                    
                    // Use a recursive function to try all fallback paths
                    const tryNextFallback = (index = 0) => {
                      if (index >= fallbacks.length) {
                        // All fallbacks failed, show a generic face placeholder
                        console.error(`All image fallbacks failed for face ${faceToRemove.id}`);
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
          </div>
        )}
        
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isRemoving}>Cancel</AlertDialogCancel>
          <AlertDialogAction 
            onClick={onRemove}
            className="bg-blue-600 hover:bg-blue-700"
            disabled={isRemoving}
          >
            {isRemoving ? (
              <>
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-r-transparent"></div>
                Removing...
              </>
            ) : "Remove from Group"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default RemoveFromGroupDialog;