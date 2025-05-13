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
              <Image
                src={faceToRemove.imageUrl}
                alt="Face to remove from group"
                fill
                className="object-cover"
              />
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