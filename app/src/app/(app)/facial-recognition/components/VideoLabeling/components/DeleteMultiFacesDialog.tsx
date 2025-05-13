import React from 'react';
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
import { Badge } from '@/components/ui/badge';
import { DetectedFace } from '../../../types';

export interface DeleteMultiFacesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedFaces: DetectedFace[];
  isDeleting: boolean;
  onDelete: () => Promise<void>;
}

const DeleteMultiFacesDialog: React.FC<DeleteMultiFacesDialogProps> = ({
  open,
  onOpenChange,
  selectedFaces,
  isDeleting,
  onDelete
}) => {
  // Count faces with and without identity codes
  const individualFacesCount = selectedFaces.filter(face => !face.identity_code).length;
  const groupedFacesCount = selectedFaces.filter(face => face.identity_code).length;
  
  // Get list of affected groups
  const affectedGroups = [...new Set(
    selectedFaces
      .filter(face => face.identity_code)
      .map(face => face.identity_code)
  )];

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Permanently Delete Multiple Faces</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to permanently delete {selectedFaces.length} face{selectedFaces.length !== 1 ? 's' : ''}? 
            This action cannot be undone and will delete the images from disk.
          </AlertDialogDescription>
          
          {groupedFacesCount > 0 && (
            <div className="mt-2 text-amber-600 font-medium text-sm">
              Note: {groupedFacesCount} of these faces belong to identity groups. 
              Deleting them will also remove them from their respective groups.
            </div>
          )}
        </AlertDialogHeader>
        
        <div className="py-4">
          <div className="flex flex-wrap gap-2 mb-3">
            <Badge variant="outline" className="bg-muted">
              {individualFacesCount} individual face{individualFacesCount !== 1 ? 's' : ''}
            </Badge>
            {groupedFacesCount > 0 && (
              <Badge variant="outline" className="bg-amber-100 text-amber-800">
                {groupedFacesCount} face{groupedFacesCount !== 1 ? 's' : ''} in groups
              </Badge>
            )}
          </div>
          
          {affectedGroups.length > 0 && (
            <div className="mt-2">
              <h4 className="text-sm font-medium mb-1">Affected Groups:</h4>
              <div className="flex flex-wrap gap-1">
                {affectedGroups.map(group => (
                  <Badge key={group} variant="secondary" className="bg-primary/20">
                    {group}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
        
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
                Deleting {selectedFaces.length} Faces...
              </>
            ) : `Permanently Delete ${selectedFaces.length} Faces`}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default DeleteMultiFacesDialog;