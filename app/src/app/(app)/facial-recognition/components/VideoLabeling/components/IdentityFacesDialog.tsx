import React from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, UserMinus } from 'lucide-react';
import { DetectedFace } from '../../../types';

export interface IdentityFacesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedIdentity: string | null;
  identityFaces: DetectedFace[];
  isLoading: boolean;
  onRemoveFromGroup: (face: DetectedFace) => void;
  formatTimestamp: (timestamp: string) => string;
}

const IdentityFacesDialog: React.FC<IdentityFacesDialogProps> = ({
  open,
  onOpenChange,
  selectedIdentity,
  identityFaces,
  isLoading,
  onRemoveFromGroup,
  formatTimestamp
}) => {
  const router = useRouter();

  // Navigate to identity management page
  const navigateToIdentity = (identityCode: string) => {
    // Close the dialog first
    onOpenChange(false);
    
    // Navigate to identity management page
    router.push(`/facial-recognition?view=identity&id=${identityCode}`);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Identity Group: {selectedIdentity}</span>
            <Badge variant="outline" className="ml-2">
              {identityFaces.length} faces
            </Badge>
          </DialogTitle>
          <DialogDescription>
            These are all the faces that belong to the same identity group.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          {isLoading ? (
            <div className="py-8 text-center">
              <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent"></div>
              <p>Loading faces...</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-h-[500px] overflow-y-auto p-2">
                {identityFaces.map(face => (
                  <div key={face.id} className="border rounded-md overflow-hidden">
                    <div className="aspect-square relative">
                      {/* Direct img tag instead of Next.js Image component for better reliability */}
                      <div className="relative w-full h-full">
                        <img
                          // Use face ID directly as the most reliable way to find the image
                          src={`/static/faces/${face.id}.jpg`}
                          alt="Face"
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
                      
                      <Button
                        size="icon"
                        variant="destructive"
                        className="absolute top-1 right-1 h-6 w-6 rounded-full bg-blue-500/70 hover:bg-blue-600/90"
                        onClick={() => onRemoveFromGroup(face)}
                      >
                        <UserMinus className="h-3 w-3 text-white" />
                      </Button>
                      
                      {face.quality_score !== undefined && (
                        <Badge 
                          variant="outline" 
                          className={`absolute bottom-1 right-1 text-xs ${
                            face.quality_score > 80 
                              ? 'bg-green-500/70 text-white border-none' 
                              : face.quality_score > 60
                                ? 'bg-yellow-500/70 text-white border-none'
                                : 'bg-red-500/70 text-white border-none'
                          }`}
                        >
                          Q: {face.quality_score}
                        </Badge>
                      )}
                    </div>
                    
                    <div className="p-2 text-xs font-medium bg-muted/30">
                      {formatTimestamp(face.timestamp)}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 text-center">
                <Button 
                  variant="outline" 
                  onClick={() => selectedIdentity && navigateToIdentity(selectedIdentity)}
                  className="mt-2"
                >
                  <Users className="mr-2 h-4 w-4" />
                  Go to Identity Management
                </Button>
              </div>
            </>
          )}
        </div>
        
        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default IdentityFacesDialog;