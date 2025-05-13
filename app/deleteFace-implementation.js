/**
 * This file contains the code to implement the delete face functionality
 * 
 * Step 1: Add this handleRemoveFace function to your component
 * Add this right after your declaration of the removeFace function
 */

// Handle face removal with confirmation
const handleRemoveFace = (e: React.MouseEvent, faceId: string) => {
  // Stop the event from triggering the face selection or other parent handlers
  e.stopPropagation();
  e.preventDefault();
  
  // Confirm before removing
  if (window.confirm('Are you sure you want to remove this face?')) {
    // Call the remove function with current video ID and face ID
    if (currentVideo) {
      removeFace(currentVideo.id, faceId);
    } else {
      toast({
        title: 'Error',
        description: 'No active video selected',
        variant: 'destructive'
      });
    }
  }
};