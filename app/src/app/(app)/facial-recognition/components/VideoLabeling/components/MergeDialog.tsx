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
import { Users } from 'lucide-react';
import { DetectedFace } from '../../../types';

interface GroupForMerge {
  identityCode: string;
  representativeFace: {
    imageUrl: string;
  };
  faceCount: number;
}

export interface MergeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedGroups: Record<string, boolean>;
  selectedFaces: Record<string, boolean>;
  faces: DetectedFace[];
  groups: {
    identityCode: string;
    representativeFace: {
      imageUrl: string;
    };
    faceCount: number;
  }[];
  isMerging: boolean;
  onMerge: () => Promise<void>;
}

const MergeDialog: React.FC<MergeDialogProps> = ({
  open,
  onOpenChange,
  selectedGroups,
  selectedFaces,
  faces,
  groups,
  isMerging,
  onMerge
}) => {
  // Calculate selected counts
  const selectedGroupCount = Object.values(selectedGroups).filter(Boolean).length;
  const selectedIndividualFacesCount = Object.entries(selectedFaces)
    .filter(([faceId, selected]) => {
      if (!selected) return false;
      const face = faces.find(f => f.id === faceId);
      return face && !face.identity_code;
    }).length;
  
  // Find selected groups
  const selectedGroupsData = groups.filter(group => selectedGroups[group.identityCode]);
  
  // Find selected individual faces
  const selectedIndividualFaces = faces.filter(face => 
    selectedFaces[face.id] && !face.identity_code
  );
  
  // Check if merge button should be disabled
  const totalSelectedItems = selectedGroupCount + selectedIndividualFacesCount;
  const isMergeDisabled = isMerging || totalSelectedItems < 2;
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Merge Groups and Faces</DialogTitle>
          <DialogDescription>
            {selectedGroupCount > 0 ? (
              <>
                You are about to merge selected items into a single identity.
                All faces will be merged into the group with the lowest ID number.
              </>
            ) : (
              <>You are about to create a new group with the selected faces.</>
            )}
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          {selectedGroupCount > 0 && (
            <>
              <h4 className="font-medium mb-2">Selected Groups:</h4>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 border rounded-md">
                {selectedGroupsData.map(group => (
                  <div key={group.identityCode} className="p-2 border rounded flex flex-col items-center">
                    <div className="relative h-24 w-24 mb-2 rounded-md overflow-hidden">
                      {/* Direct img tag with enhanced error handling for better reliability */}
                      <div className="relative w-full h-full">
                        <img
                          src={group.representativeFace.imageUrl}
                          alt="Group representative"
                          className="absolute inset-0 w-full h-full object-cover"
                          onError={(e) => {
                            console.warn(`Image not found: ${group.representativeFace.imageUrl}`);
                            
                            // Extract face ID from the URL if possible
                            const faceIdMatch = group.representativeFace.imageUrl.match(/face_id=([^&]+)/);
                            const faceId = faceIdMatch ? faceIdMatch[1] : null;
                            
                            // Try fallback paths
                            const fallbacks = [
                              // Try with direct face ID path first if we have it
                              faceId ? `/static/faces/${faceId}.jpg` : null,
                              // Try with direct URL - no image optimization
                              group.representativeFace.imageUrl.replace('/api/python-bridge?endpoint=face_image', '/static/faces'),
                              // Try with .png extension if we have face ID
                              faceId ? `/static/faces/${faceId}.png` : null,
                              // Try without optimization parameters if they exist
                              group.representativeFace.imageUrl?.split('?')[0]
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
                    <div className="font-medium">{group.identityCode}</div>
                    <div className="text-sm text-muted-foreground">{group.faceCount} faces</div>
                  </div>
                ))}
              </div>
            </>
          )}
          
          {/* Display selected individual faces */}
          {selectedIndividualFaces.length > 0 && (
            <>
              <h4 className="font-medium mb-2 mt-4">Selected Individual Faces:</h4>
              <div className="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto p-2 border rounded-md">
                {selectedIndividualFaces.map(face => (
                  <div key={face.id} className="relative h-16 w-16 rounded-md overflow-hidden">
                    {/* Direct img tag with enhanced error handling for better reliability */}
                    <div className="relative w-full h-full">
                      <img
                        // Use face ID directly as the most reliable way to find the image
                        src={`/static/faces/${face.id}.jpg`}
                        alt="Individual face"
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
            </>
          )}
          
          <div className="mt-4 p-3 bg-blue-50 text-blue-800 rounded-md">
            <p className="text-sm">
              <strong>Note:</strong> When merging, all items will be combined into the group with the lowest ID number. 
              If only individual faces are selected, a new group will be created.
              This operation cannot be undone.
            </p>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" disabled={isMerging} onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={onMerge}
            disabled={isMergeDisabled}
            className="gap-2"
          >
            {isMerging ? (
              <>
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-r-transparent"></div>
                Merging...
              </>
            ) : (
              <>
                <Users className="mr-2 h-4 w-4" />
                {selectedGroupCount > 0 ? "Confirm Merge" : "Create Group"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default MergeDialog;