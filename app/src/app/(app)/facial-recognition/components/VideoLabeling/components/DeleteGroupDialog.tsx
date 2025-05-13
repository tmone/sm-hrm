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
                <Image
                  src={groupToDelete.representativeFace.imageUrl}
                  alt="Group to delete"
                  fill
                  className="object-cover"
                />
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