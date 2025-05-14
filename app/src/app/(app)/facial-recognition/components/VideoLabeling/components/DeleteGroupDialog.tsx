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

export interface DeleteGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupToDelete: {
    identityCode: string;
    representativeFace: {
      imageUrl: string;
    };
    faceCount: number;
  } | null;
  isDeleting: boolean;
  onDelete: () => Promise<void>;
}

const DeleteGroupDialog: React.FC<DeleteGroupDialogProps> = ({
  open,
  onOpenChange,
  groupToDelete,
  isDeleting,
  onDelete
}) => {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Identity Group</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete this identity group? All {groupToDelete?.faceCount} faces will be 
            removed from this group and will revert to individual faces.
          </AlertDialogDescription>
          {groupToDelete && (
            <div className="mt-2 text-amber-600 font-medium text-sm">
              Note: This will delete identity group <span className="font-bold">{groupToDelete.identityCode}</span>{' '}
              but the face images themselves will remain as individual faces.
            </div>
          )}
        </AlertDialogHeader>
        
        {groupToDelete && (
          <div className="py-4 flex justify-center">
            <div className="relative flex flex-col items-center">
              <div className="w-40 h-40 relative rounded overflow-hidden mb-2">
                {/* Direct img tag with enhanced error handling for better reliability */}
                <div className="relative w-full h-full">
                  <img
                    src={groupToDelete.representativeFace.imageUrl}
                    alt="Group to delete"
                    className="absolute inset-0 w-full h-full object-cover"
                    onError={(e) => {
                      console.warn(`Image not found: ${groupToDelete.representativeFace.imageUrl}`);
                      
                      // Extract face ID from the URL if possible
                      const faceIdMatch = groupToDelete.representativeFace.imageUrl.match(/face_id=([^&]+)/);
                      const faceId = faceIdMatch ? faceIdMatch[1] : null;
                      
                      // Try fallback paths
                      const fallbacks = [
                        // Try with direct face ID path first if we have it
                        faceId ? `/static/faces/${faceId}.jpg` : null,
                        // Try with direct URL - no image optimization
                        groupToDelete.representativeFace.imageUrl.replace('/api/python-bridge?endpoint=face_image', '/static/faces'),
                        // Try with .png extension if we have face ID
                        faceId ? `/static/faces/${faceId}.png` : null,
                        // Try without optimization parameters if they exist
                        groupToDelete.representativeFace.imageUrl?.split('?')[0]
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
              </div>
              <div className="font-medium">{groupToDelete.identityCode}</div>
              <div className="text-sm text-muted-foreground">{groupToDelete.faceCount} faces</div>
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
            ) : "Delete Group"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default DeleteGroupDialog;