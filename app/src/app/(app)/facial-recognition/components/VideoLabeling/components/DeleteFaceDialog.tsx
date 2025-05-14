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

export interface DeleteFaceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  faceToDelete: DetectedFace | null;
  isDeleting: boolean;
  onDelete: () => Promise<void>;
}

const DeleteFaceDialog: React.FC<DeleteFaceDialogProps> = ({
  open,
  onOpenChange,
  faceToDelete,
  isDeleting,
  onDelete
}) => {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Permanently Delete Face</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to permanently delete this face? This action cannot be undone and will delete the image from disk.
          </AlertDialogDescription>
          {faceToDelete?.identity_code && (
            <div className="mt-2 text-amber-600 font-medium text-sm">
              Note: This face belongs to identity group <span className="font-bold">{faceToDelete.identity_code}</span>.
              Deleting it will also remove it from this group.
            </div>
          )}
        </AlertDialogHeader>
        
        {faceToDelete && (
          <div className="py-4 flex justify-center">
            <div className="w-40 h-40 relative rounded overflow-hidden">
              {/* Direct img tag instead of Next.js Image component for better reliability */}
              <img
                // Use face ID directly as the most reliable way to find the image
                src={`/static/faces/${faceToDelete.id}.jpg`}
                alt="Face to delete"
                className="absolute inset-0 w-full h-full object-cover"
                onError={(e) => {
                  console.warn(`Image not found: /static/faces/${faceToDelete.id}.jpg`);
                  
                  // Try fallback paths
                  const fallbacks = [
                    // Try with imageUrl from the face object
                    faceToDelete.imageUrl,
                    // Try with .png extension
                    `/static/faces/${faceToDelete.id}.png`,
                    // Try without optimization parameters if they exist
                    faceToDelete.imageUrl?.split('?')[0],
                    // Try with imageUrl field (some records use this instead)
                    faceToDelete.image_url
                  ].filter(Boolean); // Remove undefined entries
                  
                  // Use a recursive function to try all fallback paths
                  const tryNextFallback = (index = 0) => {
                    if (index >= fallbacks.length) {
                      // All fallbacks failed, show a generic face placeholder
                      console.error(`All image fallbacks failed for face ${faceToDelete.id}`);
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
        )}
        
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction 
            onClick={onDelete}
            className="bg-red-600 hover:bg-red-700"
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-r-transparent"></div>
                Deleting...
              </>
            ) : "Permanently Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default DeleteFaceDialog;