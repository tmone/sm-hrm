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
              <Image
                src={faceToDelete.imageUrl}
                alt="Face to delete"
                fill
                className="object-cover"
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