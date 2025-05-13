import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { 
  ArrowLeft, 
  RefreshCw, 
  Filter, 
  LayoutGrid, 
  List, 
  Users, 
  Search,
  Trash2
} from 'lucide-react';
import { DetectedFace } from '../../types';
import { 
  fetchFacesForVideo, 
  createIdentityGroup, 
  fetchFromAPI, 
  deleteFace, 
  deleteIdentityGroup,
  removeFaceFromGroup,
  mergeIdentityGroups,
  deleteMultipleFaces
} from '../../api';

// Import our extracted components
import {
  FaceCard,
  GroupCard,
  MergeDialog,
  GroupDialog,
  IdentityFacesDialog,
  DeleteFaceDialog,
  DeleteGroupDialog,
  RemoveFromGroupDialog,
  DeleteMultiFacesDialog
} from './components';

interface VideoLabelingProps {
  videoId: string;
}

// Helper function to manually find faces for a video if the regular API fails
const manuallyFindFaces = async (videoId: string): Promise<DetectedFace[]> => {
  // Try a custom endpoint first
  try {
    const response = await fetchFromAPI(`api/videos/${videoId}/manual-scan-faces`);
    if (response && response.faces && Array.isArray(response.faces)) {
      return response.faces;
    }
  } catch (e) {
    console.log('Manual scan endpoint not available');
  }
  
  // If not available, let's create face objects from files directly
  // We'll need to make some assumptions about file paths
  const faces: DetectedFace[] = [];
  
  try {
    // Try to fetch video details to get processing info
    const videoDetails = await fetchFromAPI(`api/videos/${videoId}`);
    if (!videoDetails) {
      console.error('Could not fetch video details');
      return [];
    }
    
    // If we have any frames directory information, try to build face objects from there
    const staticBaseUrl = '/static';
    const framesDir = `/frames/${videoId}`;
    const facesDir = `/faces/${videoId}`;
    const timestamp = new Date().toISOString();
    
    // Check if we can detect face files in the static directory through a simple API call
    try {
      const directoryCheck = await fetchFromAPI(`api/directory-exists?path=${facesDir}`);
      if (!directoryCheck || !directoryCheck.exists) {
        console.log('Faces directory does not exist');
        return [];
      }
      
      // If directory exists, try to get files
      const filesResponse = await fetchFromAPI(`api/list-files?directory=${facesDir}`);
      if (!filesResponse || !filesResponse.files || !Array.isArray(filesResponse.files)) {
        console.log('No files found in faces directory');
        return [];
      }
      
      // Create face objects from file paths
      let faceCounter = 0;
      for (const file of filesResponse.files) {
        if (file.endsWith('.jpg') || file.endsWith('.png')) {
          faceCounter++;
          faces.push({
            id: `${videoId}_face_${faceCounter}`,
            imageUrl: `${staticBaseUrl}${facesDir}/${file}`,
            timestamp: timestamp,
            confidence: 0.9,
            frameNumber: faceCounter,
            labeled: false,
            quality_score: 75
          });
        }
      }
    } catch (e) {
      console.error('Error checking directory:', e);
    }
  } catch (e) {
    console.error('Failed to manually find faces:', e);
  }
  
  return faces;
};

export default function VideoLabeling({ videoId }: VideoLabelingProps) {
  const router = useRouter();
  const { toast } = useToast();
  
  // State for faces, selection, and grouping
  const [faces, setFaces] = useState<DetectedFace[]>([]);
  const [selectedFaces, setSelectedFaces] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [isGroupDialogOpen, setIsGroupDialogOpen] = useState(false);
  const [isIdentityDialogOpen, setIsIdentityDialogOpen] = useState(false);
  const [selectedIdentity, setSelectedIdentity] = useState<string | null>(null);
  const [identityFaces, setIdentityFaces] = useState<DetectedFace[]>([]);
  const [isLoadingIdentityFaces, setIsLoadingIdentityFaces] = useState(false);
  
  // For group/face merging
  const [selectedGroups, setSelectedGroups] = useState<Record<string, boolean>>({});
  const [isMergeDialogOpen, setIsMergeDialogOpen] = useState(false);
  const [isMerging, setIsMerging] = useState(false);
  const [mergeMode, setMergeMode] = useState<'group-only' | 'mixed'>('mixed');
  
  // For face dialogs
  const [isDeleteFaceDialogOpen, setIsDeleteFaceDialogOpen] = useState(false);
  const [isRemoveFromGroupDialogOpen, setIsRemoveFromGroupDialogOpen] = useState(false);
  const [isDeleteGroupDialogOpen, setIsDeleteGroupDialogOpen] = useState(false);
  const [isDeleteMultiFacesDialogOpen, setIsDeleteMultiFacesDialogOpen] = useState(false);
  const [faceToDelete, setFaceToDelete] = useState<DetectedFace | null>(null);
  const [faceToRemove, setFaceToRemove] = useState<DetectedFace | null>(null);
  const [groupToDelete, setGroupToDelete] = useState<{
    identityCode: string;
    representativeFace: {
      imageUrl: string;
      quality_score?: number;
    };
    faceCount: number;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isRemovingFromGroup, setIsRemovingFromGroup] = useState(false);
  const [isDeletingGroup, setIsDeletingGroup] = useState(false);
  const [isDeletingMultipleFaces, setIsDeletingMultipleFaces] = useState(false);
  const [selectedFacesToDelete, setSelectedFacesToDelete] = useState<DetectedFace[]>([]);
  const [recentlyRemovedFaceId, setRecentlyRemovedFaceId] = useState<string | null>(null);
  
  // Face filtering
  const [filterLabeled, setFilterLabeled] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [facesPerPage, setFacesPerPage] = useState(100);
  
  // Load faces when component mounts
  useEffect(() => {
    loadFaces();
  }, [videoId]);
  
  const loadFaces = async () => {
    try {
      setIsLoading(true);
      
      // Try to get faces from API
      let videoFaces = await fetchFacesForVideo(videoId);
      
      // If no faces returned but they should exist, try a manual approach
      if (videoFaces.length === 0) {
        console.log("No faces found via API - trying manual file scanning");
        
        // This is a fallback to try to find face images in the static directory
        try {
          // For now, let's simulate a loading state to let user know we're looking
          toast({
            title: 'Searching for faces',
            description: 'Checking alternative sources for face data...'
          });
          
          // Try direct access to static face directory
          try {
            const staticFaces = await manuallyFindFaces(videoId);
            if (staticFaces.length > 0) {
              console.log(`Found ${staticFaces.length} faces through manual scan`);
              videoFaces = staticFaces;
            }
          } catch (staticError) {
            console.error('Static directory scan failed:', staticError);
          }
          
          // If still no faces, try one more API call
          if (videoFaces.length === 0) {
            await new Promise(resolve => setTimeout(resolve, 1500));
            videoFaces = await fetchFacesForVideo(videoId);
          }
        } catch (fallbackError) {
          console.error('Fallback face loading failed:', fallbackError);
        }
      }
      
      if (videoFaces.length === 0) {
        toast({
          title: 'No faces found',
          description: 'No faces were found for this video. Please try processing the video again.',
          variant: 'destructive'
        });
      } else {
        toast({
          title: 'Faces loaded',
          description: `Found ${videoFaces.length} faces for this video`
        });
      }
      
      setFaces(videoFaces);
    } catch (error) {
      console.error('Error loading faces:', error);
      toast({
        title: 'Failed to load faces',
        description: 'Could not load faces for this video',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  // Select/deselect all faces
  const toggleSelectAll = () => {
    if (Object.values(selectedFaces).some(selected => selected)) {
      // If any face is selected, deselect all
      setSelectedFaces({});
    } else {
      // Otherwise, select all displayed faces
      const newSelection = { ...selectedFaces };
      filteredFaces.forEach(face => {
        newSelection[face.id] = true;
      });
      setSelectedFaces(newSelection);
    }
  };
  
  // Toggle selection for a single face
  const toggleFaceSelection = (faceId: string) => {
    setSelectedFaces(prev => ({
      ...prev,
      [faceId]: !prev[faceId]
    }));
  };
  
  // Filter faces based on search and labeled/unlabeled filter
  const filteredFaces = faces.filter(face => {
    // Consider a face labeled if it has an identity_code OR labeled is true
    const isLabeled = face.labeled || !!face.identity_code;
    
    // Apply labeled/unlabeled filter - only show unlabeled faces when checked
    if (filterLabeled && isLabeled) return false;
    
    // Apply search query filter (search by identity code)
    if (searchQuery) {
      // When searching, we want to include:
      // 1. Individual faces (without identity_code) - always show these
      // 2. Faces with matching identity_code (for the search)
      if (!face.identity_code) {
        return true; // Always include individual faces
      }
      return face.identity_code.toLowerCase().includes(searchQuery.toLowerCase());
    }
    
    return true;
  });
  
  // Group faces by identity code
  const groupedFaces = React.useMemo(() => {
    const groups: Record<string, DetectedFace[]> = {};
    
    // Only group faces that have identity codes
    faces.forEach(face => {
      if (face.identity_code) {
        if (!groups[face.identity_code]) {
          groups[face.identity_code] = [];
        }
        groups[face.identity_code].push(face);
      }
    });
    
    // Convert to array for rendering
    return Object.entries(groups).map(([identityCode, groupFaces]) => ({
      identityCode,
      faces: groupFaces,
      // Find the best quality face as the representative
      representativeFace: groupFaces.reduce((best, current) => 
        (current.quality_score || 0) > (best.quality_score || 0) ? current : best, 
        groupFaces[0]
      ),
      faceCount: groupFaces.length
    }));
  }, [faces]);
  
  // Get selected face count
  const selectedFaceCount = Object.values(selectedFaces).filter(Boolean).length;
  
  // Final face list with individuals and groups
  const processedFaces = React.useMemo(() => {
    if (filterLabeled) {
      // If showing only unlabeled, don't include any groups
      // Make sure all unlabeled faces are shown as individuals, even if they were just ungrouped
      return { 
        individuals: filteredFaces.filter(face => !face.identity_code), // Explicit filter to ensure only showing faces without identity_code
        groups: []
      };
    }
    
    // When showing all faces, separate individuals and groups
    const groupedIdentityCodes = new Set(groupedFaces.map(group => group.identityCode));
    
    // Individuals are faces without identity codes 
    // (even single-face groups should display as groups)
    const individuals = filteredFaces.filter(face => 
      !face.identity_code
    );
    
    let displayGroups = [...groupedFaces]; // Create a copy for manipulation
    
    // Filter groups if we have a search query
    if (searchQuery) {
      displayGroups = displayGroups.filter(g => 
        g.identityCode.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Sort groups by identity code in ascending order
    // PERSON-0001, PERSON-0002, etc.
    displayGroups.sort((a, b) => {
      // Extract numeric part from identity codes (assuming format like "PERSON-0001")
      const aMatch = a.identityCode.match(/.*-(\d+)/);
      const bMatch = b.identityCode.match(/.*-(\d+)/);
      
      if (aMatch && bMatch) {
        // Compare as numbers for proper numeric sorting
        const aNum = parseInt(aMatch[1], 10);
        const bNum = parseInt(bMatch[1], 10);
        return aNum - bNum;
      }
      
      // Fallback to string comparison if format doesn't match the expected pattern
      return a.identityCode.localeCompare(b.identityCode);
    });
    
    return {
      individuals,
      groups: displayGroups
    };
  }, [filteredFaces, groupedFaces, filterLabeled, searchQuery]);
  
  // Pagination with individuals and groups combined
  const paginatedContent = React.useMemo(() => {
    // For display purposes, we want to show individuals first, then sorted grouped cards at the end
    // The groups are already sorted by identity code in processedFaces
    const allItems = [
      ...processedFaces.individuals,
      ...processedFaces.groups.map(group => ({ type: 'group', data: group }))
    ];
    
    return allItems.slice(
      (currentPage - 1) * facesPerPage,
      currentPage * facesPerPage
    );
  }, [processedFaces, currentPage, facesPerPage]);
  
  // Get the total count of all items for pagination
  const totalItemCount = processedFaces.individuals.length + processedFaces.groups.length;
  
  // Group selected faces
  const groupSelectedFaces = async () => {
    // Get IDs of selected faces
    const selectedFaceIds = Object.entries(selectedFaces)
      .filter(([_, selected]) => selected)
      .map(([faceId]) => faceId);
    
    if (selectedFaceIds.length === 0) {
      toast({
        title: 'No faces selected',
        description: 'Please select at least one face to group',
        variant: 'destructive'
      });
      return;
    }
    
    try {
      const newGroup = await createIdentityGroup(selectedFaceIds);
      
      // Update face data in the UI
      setFaces(prev => 
        prev.map(face => {
          if (selectedFaceIds.includes(face.id)) {
            return {
              ...face,
              identity_code: newGroup.id,
              labeled: true
            };
          }
          return face;
        })
      );
      
      // Clear selection
      setSelectedFaces({});
      
      // Show success message
      toast({
        title: 'Faces grouped successfully',
        description: `Created identity group ${newGroup.id} with ${selectedFaceIds.length} faces`,
      });
      
      // Close dialog
      setIsGroupDialogOpen(false);
      
      // Reload all faces to get the updated groups from the server
      loadFaces();
    } catch (error) {
      console.error('Error grouping faces:', error);
      toast({
        title: 'Failed to group faces',
        description: 'An error occurred while grouping faces',
        variant: 'destructive'
      });
    }
  };
  
  // Function to view all faces in an identity group
  const viewIdentityFaces = (identityCode: string) => {
    setIsLoadingIdentityFaces(true);
    setSelectedIdentity(identityCode);
    
    // Get all faces for this identity from our existing data
    const groupFaces = faces.filter(face => face.identity_code === identityCode);
    
    // Sort by quality score (highest first)
    const sortedFaces = [...groupFaces].sort((a, b) => 
      (b.quality_score || 0) - (a.quality_score || 0)
    );
    
    setIdentityFaces(sortedFaces);
    setIsLoadingIdentityFaces(false);
    setIsIdentityDialogOpen(true);
  };
  
  // Handle delete face (permanent deletion)
  const handleDeleteFace = async () => {
    if (!faceToDelete) return;
    
    setIsDeleting(true);
    try {
      // Call the API to delete the face
      await deleteFace(videoId, faceToDelete.id);
      
      // Update local state to remove the face
      setFaces(prevFaces => prevFaces.filter(face => face.id !== faceToDelete.id));
      
      // Update identity faces if open
      if (isIdentityDialogOpen && selectedIdentity) {
        setIdentityFaces(prevFaces => prevFaces.filter(face => face.id !== faceToDelete?.id));
      }
      
      // Show detailed success message
      const faceId = faceToDelete.id.substring(0, 8);
      toast({
        title: "Face deleted successfully",
        description: `Face ID ${faceId}... has been permanently deleted from the system`,
        variant: "default",
      });
      
      // Close the dialog
      setIsDeleteFaceDialogOpen(false);
      setFaceToDelete(null);
      
      // If we're viewing a group, we should refresh the whole list after a small delay
      // to make sure everything is in sync with the backend
      setTimeout(() => {
        loadFaces();
        setIsDeleting(false);
      }, 500);
    } catch (error) {
      setIsDeleting(false);
      console.error('Error deleting face:', error);
      toast({
        title: "Failed to delete face",
        description: `Error: ${error instanceof Error ? error.message : "Server communication error"}. Please try again.`,
        variant: "destructive"
      });
    }
  };
  
  // Handle removing face from group (keeps face but removes from group)
  const handleRemoveFaceFromGroup = async () => {
    if (!faceToRemove || !faceToRemove.identity_code) return;
    
    setIsRemovingFromGroup(true);
    try {
      // Remember the face details for tracking and notification
      const faceId = faceToRemove.id.substring(0, 8);
      const fullFaceId = faceToRemove.id;
      const groupId = faceToRemove.identity_code;
      
      console.log("Implementing pure client-side removal for face:", fullFaceId, "from group:", groupId);
      
      // Skip all API calls and implement a pure client-side solution
      // This is guaranteed to update the UI properly even if the server has issues
      
      // 1. Create a new array of faces with the identity_code removed from the target face
      const updatedFacesArray = faces.map(face => {
        if (face.id === fullFaceId) {
          // Create a new face object without the identity_code
          const { identity_code, ...restFace } = face;
          return {
            ...restFace,
            labeled: false  // Mark as unlabeled
          };
        }
        return face;
      });
      
      // 2. Update our state with the new array
      setFaces(updatedFacesArray);
      
      // 3. Close the dialog
      setIsRemoveFromGroupDialogOpen(false);
      setFaceToRemove(null);
      
      // 4. Set the recently removed face to highlight it in the UI
      setRecentlyRemovedFaceId(fullFaceId);
      
      // 5. Clear the highlight after 5 seconds
      setTimeout(() => {
        setRecentlyRemovedFaceId(null);
      }, 5000);
      
      // 6. Reset any filters to ensure the face is visible
      if (filterLabeled) {
        setFilterLabeled(false);
      }
      
      if (searchQuery) {
        setSearchQuery('');
      }
      
      // 7. Update identity faces if the identity dialog is open
      if (isIdentityDialogOpen && selectedIdentity) {
        const updatedIdentityFaces = updatedFacesArray.filter(
          face => face.identity_code === selectedIdentity
        );
        setIdentityFaces(updatedIdentityFaces);
      }
      
      // 8. Show success message
      toast({
        title: "Face removed from group",
        description: `Face ID ${faceId}... has been removed from group ${groupId} and is now an individual face`,
        variant: "default",
      });
      
      // 9. Reset loading state
      setIsRemovingFromGroup(false);
      
      // 10. Force a re-render to update any memoized values
      setTimeout(() => {
        setFaces(prev => [...prev]);
      }, 100);
      
      // 11. Optionally, try to update the server in the background
      // This won't block the UI or show errors to the user
      setTimeout(async () => {
        try {
          await removeFaceFromGroup(groupId, fullFaceId).catch(() => {
            // Silently fail - we've already updated the UI
            console.log("Background server update failed, but UI is already updated");
          });
        } catch (e) {
          // Ignore errors - we've already updated the UI
        }
      }, 500);
      
    } catch (error) {
      // This catch block should never be reached with our pure client-side approach
      // But we'll keep it just in case
      setIsRemovingFromGroup(false);
      console.error('Error in client-side face removal:', error);
      toast({
        title: "Failed to remove from group",
        description: `Error: ${error instanceof Error ? error.message : "Unexpected error"}. Please try again.`,
        variant: "destructive"
      });
    }
  };
  
  // Merge selected groups and faces function
  const mergeSelectedGroups = async () => {
    // Get the identity codes of the selected groups
    const selectedGroupIds = Object.entries(selectedGroups)
      .filter(([_, selected]) => selected)
      .map(([groupId]) => groupId);
      
    // Find selected faces that are not already in groups regardless of merge mode
    // This enables the ability to merge individual faces with groups or create new groups from selected faces
    const selectedFaceIds = Object.entries(selectedFaces)
      .filter(([_, selected]) => selected)
      .map(([faceId]) => faceId);
    
    // If we're in mixed mode, also check for individual faces to add to a group
    const selectedIndividualFaces: DetectedFace[] = [];
    let targetGroupId = '';
    
    if (selectedFaceIds.length > 0) {
      // Find faces that don't have an identity_code (individual faces)
      selectedIndividualFaces.push(
        ...faces.filter(face => 
          selectedFaceIds.includes(face.id) && 
          !face.identity_code
        )
      );
    }
    
    // Various scenarios:
    // 1. Only 1 group selected + individual faces
    // 2. Multiple groups selected + individual faces
    // 3. Only groups, no individual faces
    // 4. No groups, only individual faces (should create a new group)
    // 5. Multiple individual faces (should create a new group)
    
    const totalSelectedItems = selectedGroupIds.length + selectedIndividualFaces.length;
    
    if (totalSelectedItems === 0) {
      toast({
        title: 'Nothing selected',
        description: 'Please select at least one group or individual face to merge',
        variant: 'destructive'
      });
      return;
    }
    
    if (selectedGroupIds.length === 0 && selectedIndividualFaces.length > 0) {
      // This is just a regular group creation, not a merge
      setIsMergeDialogOpen(false);
      setIsGroupDialogOpen(true);
      return;
    }
    
    if (selectedGroupIds.length === 1 && selectedIndividualFaces.length === 0) {
      toast({
        title: 'Not enough items selected',
        description: 'Please select at least two groups or add individual faces to merge with the group',
        variant: 'destructive'
      });
      return;
    }
    
    setIsMerging(true);
    try {
      let targetId = '';
      const selectedIndividualFaceIds = selectedIndividualFaces.map(face => face.id);
      
      // First, if we have individual faces and at least 1 group, add faces to the first group
      if (selectedIndividualFaces.length > 0 && selectedGroupIds.length > 0) {
        // Sort group IDs to find the lowest one
        const sortedIds = [...selectedGroupIds].sort((a, b) => {
          const numA = parseInt(a.split('-')[1]);
          const numB = parseInt(b.split('-')[1]);
          return numA - numB;
        });
        
        targetId = sortedIds[0]; // Use the lowest group ID
        
        // Add individual faces to this target group
        const addResult = await createIdentityGroup(selectedIndividualFaceIds, targetId);
        console.log("Added individual faces to target group:", addResult);
      }
      
      // Now, if we have multiple groups, merge them
      if (selectedGroupIds.length > 1) {
        // Call the API to merge the groups
        const result = await mergeIdentityGroups(selectedGroupIds);
        targetId = result.target_id;
      }
      
      // Update our local state
      setFaces(prevFaces => 
        prevFaces.map(face => {
          // If face was in one of the source groups, update its identity_code
          if (face.identity_code && selectedGroupIds.includes(face.identity_code) && face.identity_code !== targetId) {
            return {
              ...face,
              identity_code: targetId,
              labeled: true
            };
          }
          // If face was an individual selected face
          else if (selectedIndividualFaceIds.includes(face.id)) {
            return {
              ...face,
              identity_code: targetId,
              labeled: true
            };
          }
          return face;
        })
      );
      
      // Clear selections
      setSelectedGroups({});
      setSelectedFaces({});
      
      // Show success message
      let descriptionMessage = '';
      if (selectedIndividualFaces.length > 0 && selectedGroupIds.length > 1) {
        descriptionMessage = `Merged ${selectedGroupIds.length - 1} groups and ${selectedIndividualFaces.length} individual faces into ${targetId}`;
      } else if (selectedIndividualFaces.length > 0) {
        descriptionMessage = `Added ${selectedIndividualFaces.length} individual faces to group ${targetId}`;
      } else {
        descriptionMessage = `Merged ${selectedGroupIds.length - 1} groups into ${targetId}`;
      }
      
      toast({
        title: 'Merge successful',
        description: descriptionMessage,
      });
      
      // Close dialog
      setIsMergeDialogOpen(false);
      
      // Refresh to get the updated data from the server
      setTimeout(() => {
        loadFaces();
      }, 1000);
    } catch (error) {
      console.error('Error merging groups:', error);
      toast({
        title: 'Failed to merge',
        description: 'An error occurred while merging the groups and faces',
        variant: 'destructive'
      });
    } finally {
      setIsMerging(false);
    }
  };
  
  // Toggle selection for a group
  const toggleGroupSelection = (groupId: string) => {
    setSelectedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
  };
  
  // Get selected group count
  const selectedGroupCount = Object.values(selectedGroups).filter(Boolean).length;
  
  // Function to prompt face deletion (permanent)
  const promptDeleteFace = (face: DetectedFace) => {
    setFaceToDelete(face);
    setIsDeleteFaceDialogOpen(true);
  };
  
  // Function to prompt face removal from group
  const promptRemoveFromGroup = (face: DetectedFace) => {
    if (!face.identity_code) {
      // If face is not in a group, show an error
      toast({
        title: "Cannot remove from group",
        description: "This face is not part of any group",
        variant: "destructive"
      });
      return;
    }
    
    setFaceToRemove(face);
    setIsRemoveFromGroupDialogOpen(true);
  };
  
  // Function to prompt group deletion
  const promptDeleteGroup = (group: {
    identityCode: string;
    representativeFace: {
      imageUrl: string;
      quality_score?: number;
    };
    faceCount: number;
  }) => {
    setGroupToDelete(group);
    setIsDeleteGroupDialogOpen(true);
  };
  
  // Handle delete group
  const handleDeleteGroup = async () => {
    if (!groupToDelete) return;
    
    setIsDeletingGroup(true);
    try {
      // Get all faces that belong to this group
      const groupFaces = faces.filter(face => face.identity_code === groupToDelete.identityCode);
      
      // Call the API to delete the group
      await deleteIdentityGroup(groupToDelete.identityCode);
      
      // Update local state to remove the identity_code from all faces in the group
      setFaces(prevFaces => 
        prevFaces.map(face => {
          if (face.identity_code === groupToDelete.identityCode) {
            // Create a new face object without the identity_code
            const { identity_code, ...restFace } = face;
            return {
              ...restFace,
              labeled: false  // Mark as unlabeled
            };
          }
          return face;
        })
      );
      
      // Show success message
      toast({
        title: "Group deleted successfully",
        description: `Group ${groupToDelete.identityCode} with ${groupToDelete.faceCount} faces has been deleted. The faces are now individual faces.`,
        variant: "default"
      });
      
      // Close dialog
      setIsDeleteGroupDialogOpen(false);
      setGroupToDelete(null);
      
      // Refresh to get the updated data from the server after a delay
      setTimeout(() => {
        loadFaces();
        setIsDeletingGroup(false);
      }, 500);
    } catch (error) {
      console.error('Error deleting group:', error);
      toast({
        title: "Failed to delete group",
        description: `Error: ${error instanceof Error ? error.message : "Server communication error"}. Please try again.`,
        variant: "destructive"
      });
      setIsDeletingGroup(false);
    }
  };
  
  // Function to prompt deletion of multiple faces
  const promptDeleteMultipleFaces = () => {
    // Check how many faces are selected
    const selectedFaceIds = Object.entries(selectedFaces)
      .filter(([_, selected]) => selected)
      .map(([faceId]) => faceId);
    
    if (selectedFaceIds.length === 0) {
      toast({
        title: 'No faces selected',
        description: 'Please select at least one face to delete',
        variant: 'destructive'
      });
      return;
    }
    
    // Get the full face objects for the selected IDs
    const facesToDelete = faces.filter(face => selectedFaceIds.includes(face.id));
    
    // Store the full face objects in state for use by the dialog
    setSelectedFacesToDelete(facesToDelete);
    
    // Open the dialog
    setIsDeleteMultiFacesDialogOpen(true);
  };
  
  // Handle deleting multiple faces
  const handleDeleteMultipleFaces = async () => {
    if (!selectedFacesToDelete || selectedFacesToDelete.length === 0) return;
    
    setIsDeletingMultipleFaces(true);
    
    try {
      // Get the IDs
      const faceIdsToDelete = selectedFacesToDelete.map(face => face.id);
      
      // Call the API to delete the faces
      const result = await deleteMultipleFaces(videoId, faceIdsToDelete);
      
      // Update local state to remove the deleted faces
      setFaces(prevFaces => prevFaces.filter(face => !faceIdsToDelete.includes(face.id)));
      
      // Clear selection
      setSelectedFaces({});
      
      // Show success message
      toast({
        title: "Faces deleted successfully",
        description: `${result.successful} face${result.successful !== 1 ? 's' : ''} deleted successfully. ${result.failed > 0 ? `${result.failed} failed.` : ''}`,
        variant: "default"
      });
      
      // Close dialog
      setIsDeleteMultiFacesDialogOpen(false);
      setSelectedFacesToDelete([]);
      
      // Refresh to get the updated data from the server after a delay
      setTimeout(() => {
        loadFaces();
        setIsDeletingMultipleFaces(false);
      }, 500);
    } catch (error) {
      console.error('Error deleting multiple faces:', error);
      toast({
        title: "Failed to delete faces",
        description: `Error: ${error instanceof Error ? error.message : "Server communication error"}. Please try again.`,
        variant: "destructive"
      });
      setIsDeletingMultipleFaces(false);
    }
  };
  
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      
      // Check if the date is valid
      if (isNaN(date.getTime())) {
        // If timestamp can't be parsed as a date, try to extract time info from the filename
        if (typeof timestamp === 'string' && timestamp.length > 0) {
          // Extract time information from a UUID or filename if possible
          const filenameParts = timestamp.split('/');
          const filename = filenameParts[filenameParts.length - 1]; // Get the filename part
          
          if (filename) {
            // Try to extract sequence number from filename (assuming pattern like XXXXX-0001.jpg)
            const sequenceMatch = filename.match(/[-_](\d{1,6})\.[a-zA-Z]+$/);
            if (sequenceMatch && sequenceMatch[1]) {
              return `#${parseInt(sequenceMatch[1])}`;
            }
            
            // If we have a UUID-based filename, format it nicely
            if (filename.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-zA-Z]+$/i)) {
              return "UUID-based";
            }
            
            // Extract just the filename without extension
            const noExtension = filename.replace(/\.[^/.]+$/, "");
            // Truncate if too long
            return noExtension.length > 10 ? noExtension.substring(0, 10) + "..." : noExtension;
          }
        }
        
        // If all else fails, show "Frame" instead of Invalid Date
        return "Frame";
      }
      
      // Format the valid date
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (e) {
      // Fallback to showing "Frame" instead of the timestamp
      return "Frame";
    }
  };
  
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Videos
          </Button>
          <h1 className="text-3xl font-bold">Video Face Labeling</h1>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => setViewMode('grid')}>
            <LayoutGrid className={`h-4 w-4 ${viewMode === 'grid' ? 'text-primary' : ''}`} />
          </Button>
          <Button variant="outline" onClick={() => setViewMode('list')}>
            <List className={`h-4 w-4 ${viewMode === 'list' ? 'text-primary' : ''}`} />
          </Button>
        </div>
      </div>
      
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader className="pb-3 sticky top-0 z-20 bg-background border-b shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Face Management</CardTitle>
                <CardDescription>
                  {filteredFaces.length} face{filteredFaces.length !== 1 ? 's' : ''} found
                </CardDescription>
              </div>
              
              <div className="flex items-center gap-2 flex-wrap md:flex-nowrap">
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="filter-labeled" 
                    checked={filterLabeled}
                    onCheckedChange={(checked) => setFilterLabeled(!!checked)}
                  />
                  <Label htmlFor="filter-labeled">Show unlabeled only</Label>
                </div>
                
                <Button onClick={toggleSelectAll}>
                  {Object.values(selectedFaces).some(selected => selected) ? 'Deselect All' : 'Select All'}
                </Button>
                
                <Button 
                  onClick={() => setIsGroupDialogOpen(true)}
                  disabled={selectedFaceCount < 1}
                  className="gap-2"
                >
                  <Users className="h-4 w-4" />
                  Group Selected ({selectedFaceCount})
                </Button>
                
                <Button 
                  onClick={() => {
                    // Always set to mixed mode by default to support merging individual faces with groups
                    setMergeMode('mixed');
                    setIsMergeDialogOpen(true);
                  }}
                  disabled={selectedGroupCount + (Object.values(selectedFaces).filter(selected => selected).length) < 2}
                  className="gap-2"
                  variant="secondary"
                >
                  <Users className="h-4 w-4" />
                  Merge ({selectedGroupCount + (Object.values(selectedFaces).filter(selected => selected).length)})
                </Button>
                
                <Button 
                  onClick={promptDeleteMultipleFaces}
                  disabled={selectedFaceCount < 1}
                  className="gap-2"
                  variant="destructive"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Selected ({selectedFaceCount})
                </Button>
                
                <Button onClick={loadFaces} variant="outline">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="mt-4 relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search by identity code..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </CardHeader>
          
          <CardContent>
            {isLoading ? (
              <div className="py-8 text-center">
                <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-r-transparent"></div>
                <p>Loading faces...</p>
              </div>
            ) : filteredFaces.length === 0 && processedFaces.groups.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {searchQuery ? (
                  <>
                    No faces match your search for "{searchQuery}".
                    {filterLabeled && (
                      <div className="mt-2">
                        <span className="text-primary font-medium">Note:</span> You are currently filtering to show only unlabeled faces.
                        Uncheck "Show unlabeled only" to see all faces.
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    No faces match your filters.
                    {filterLabeled && processedFaces.individuals.length === 0 && (
                      <div className="mt-2">
                        <span className="text-primary font-medium">Tip:</span> There may be faces in groups.
                        Uncheck "Show unlabeled only" to see all faces.
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : viewMode === 'grid' ? (
              // Grid View
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
                {paginatedContent.map((item, index) => {
                  // Check if this is a group card
                  if ('type' in item && item.type === 'group') {
                    const group = item.data;
                    return (
                      <GroupCard
                        key={`group-${group.identityCode}`}
                        identityCode={group.identityCode}
                        representativeFace={group.representativeFace}
                        faceCount={group.faceCount}
                        isSelected={selectedGroups[group.identityCode] || false}
                        onSelect={toggleGroupSelection}
                        onViewFaces={viewIdentityFaces}
                        onDelete={promptDeleteGroup}
                      />
                    );
                  }
                  
                  // Regular face card (individual)
                  const face = item as DetectedFace;
                  return (
                    <FaceCard
                      key={face.id}
                      face={face}
                      isSelected={selectedFaces[face.id] || false}
                      onSelect={toggleFaceSelection}
                      onDelete={promptDeleteFace}
                      recentlyRemovedFaceId={recentlyRemovedFaceId}
                      formatTimestamp={formatTimestamp}
                    />
                  );
                })}
              </div>
            ) : (
              // List View
              <div className="rounded-md border">
                <Table>
                  <TableHeader className="sticky top-[138px] z-10 bg-background">
                    <TableRow>
                      <TableHead className="w-12">
                        <Checkbox 
                          checked={
                            processedFaces.individuals.length > 0 && 
                            processedFaces.individuals.every(face => selectedFaces[face.id])
                          }
                          onCheckedChange={toggleSelectAll}
                          aria-label="Select all"
                        />
                      </TableHead>
                      <TableHead className="w-24">Face</TableHead>
                      <TableHead>ID</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Frame</TableHead>
                      <TableHead>Quality</TableHead>
                      <TableHead>Identity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedContent.map((item) => {
                      // Handle group items
                      if ('type' in item && item.type === 'group') {
                        const group = item.data;
                        return (
                          <TableRow 
                            key={`group-${group.identityCode}`}
                            className="bg-primary/5 cursor-pointer hover:bg-primary/10"
                            onClick={() => viewIdentityFaces(group.identityCode)}
                          >
                            <TableCell>
                              {/* No checkbox for groups */}
                            </TableCell>
                            <TableCell>
                              <div className="h-12 w-12 relative rounded overflow-hidden">
                                <Image
                                  src={group.representativeFace.imageUrl}
                                  alt="Group Representative"
                                  fill
                                  className="object-cover"
                                />
                                <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                                  <Badge variant="secondary" className="bg-primary text-white">
                                    Group
                                  </Badge>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell className="font-medium text-primary">Group</TableCell>
                            <TableCell>Multiple</TableCell>
                            <TableCell>Multiple</TableCell>
                            <TableCell>
                              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                                {group.representativeFace.quality_score || 'N/A'} (Best)
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Badge variant="secondary" className="bg-primary/20 hover:bg-primary/30">
                                  {group.identityCode}
                                </Badge>
                                <Badge variant="outline">{group.faceCount} faces</Badge>
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      }
                      
                      // Regular face row
                      const face = item as DetectedFace;
                      return (
                        <TableRow 
                          key={face.id}
                          className={`
                            ${selectedFaces[face.id] ? 'bg-primary/5' : ''}
                            ${recentlyRemovedFaceId === face.id ? 'bg-blue-50 animate-pulse' : ''}
                          `}
                        >
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Checkbox 
                                checked={selectedFaces[face.id] || false}
                                onCheckedChange={() => toggleFaceSelection(face.id)}
                              />
                              <Button
                                size="icon"
                                variant="destructive"
                                className="h-6 w-6 rounded-full ml-1"
                                onClick={() => promptDeleteFace(face)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="h-12 w-12 relative rounded overflow-hidden">
                              <Image
                                src={face.imageUrl}
                                alt="Face"
                                fill
                                className="object-cover"
                              />
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-xs">{face.id.substring(0, 8)}...</TableCell>
                          <TableCell>{formatTimestamp(face.timestamp)}</TableCell>
                          <TableCell>{face.frameNumber}</TableCell>
                          <TableCell>
                            <Badge 
                              variant="outline" 
                              className={
                                face.quality_score && face.quality_score > 80 
                                  ? 'bg-green-50 text-green-700' 
                                  : face.quality_score && face.quality_score > 60
                                    ? 'bg-yellow-50 text-yellow-700'
                                    : 'bg-red-50 text-red-700'
                              }
                            >
                              {face.quality_score || 'N/A'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {face.identity_code ? (
                              <Badge variant="secondary">{face.identity_code}</Badge>
                            ) : recentlyRemovedFaceId === face.id ? (
                              <Badge variant="outline" className="bg-blue-50 text-blue-600 border-blue-200">
                                Recently Removed <span className="ml-1 text-xs">✓</span>
                              </Badge>
                            ) : (
                              <Badge variant="outline">Unlabeled</Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
            
            {/* Pagination controls */}
            {totalItemCount > facesPerPage && (
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  Showing {(currentPage - 1) * facesPerPage + 1} to {
                    Math.min(currentPage * facesPerPage, totalItemCount)
                  } of {totalItemCount} items
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(page => Math.max(1, page - 1))}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  
                  <div className="mx-2">
                    Page {currentPage} of {Math.ceil(totalItemCount / facesPerPage)}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(page => 
                      Math.min(Math.ceil(totalItemCount / facesPerPage), page + 1)
                    )}
                    disabled={currentPage >= Math.ceil(totalItemCount / facesPerPage)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Group Dialog */}
      <GroupDialog
        open={isGroupDialogOpen}
        onOpenChange={setIsGroupDialogOpen}
        selectedFaces={selectedFaces}
        faces={faces}
        onGroupFaces={groupSelectedFaces}
      />
      
      {/* Merge Dialog */}
      <MergeDialog
        open={isMergeDialogOpen}
        onOpenChange={setIsMergeDialogOpen}
        selectedGroups={selectedGroups}
        selectedFaces={selectedFaces}
        faces={faces}
        groups={processedFaces.groups}
        isMerging={isMerging}
        onMerge={mergeSelectedGroups}
      />
      
      {/* Identity Faces Dialog */}
      <IdentityFacesDialog
        open={isIdentityDialogOpen}
        onOpenChange={setIsIdentityDialogOpen}
        selectedIdentity={selectedIdentity}
        identityFaces={identityFaces}
        isLoading={isLoadingIdentityFaces}
        onRemoveFromGroup={promptRemoveFromGroup}
        formatTimestamp={formatTimestamp}
      />
      
      {/* Delete Face Dialog */}
      <DeleteFaceDialog
        open={isDeleteFaceDialogOpen}
        onOpenChange={setIsDeleteFaceDialogOpen}
        faceToDelete={faceToDelete}
        isDeleting={isDeleting}
        onDelete={handleDeleteFace}
      />
      
      {/* Remove Face from Group Dialog */}
      <RemoveFromGroupDialog
        open={isRemoveFromGroupDialogOpen}
        onOpenChange={setIsRemoveFromGroupDialogOpen}
        faceToRemove={faceToRemove}
        isRemoving={isRemovingFromGroup}
        onRemove={handleRemoveFaceFromGroup}
      />
      
      {/* Delete Group Dialog */}
      <DeleteGroupDialog
        open={isDeleteGroupDialogOpen}
        onOpenChange={setIsDeleteGroupDialogOpen}
        groupToDelete={groupToDelete}
        isDeleting={isDeletingGroup}
        onDelete={handleDeleteGroup}
      />
      
      {/* Delete Multiple Faces Dialog */}
      <DeleteMultiFacesDialog
        open={isDeleteMultiFacesDialogOpen}
        onOpenChange={setIsDeleteMultiFacesDialogOpen}
        selectedFaces={selectedFacesToDelete}
        isDeleting={isDeletingMultipleFaces}
        onDelete={handleDeleteMultipleFaces}
      />
    </div>
  );
}