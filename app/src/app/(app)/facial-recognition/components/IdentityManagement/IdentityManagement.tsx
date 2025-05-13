import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
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
import { Users, Search, Tag, UserPlus, Trash2, GitMerge } from 'lucide-react';
import { IdentityGroup, DetectedFace } from '../../types';
import { 
  fetchIdentityGroups, 
  addFacesToIdentity, 
  labelFace, 
  createIdentityGroup, 
  fetchFromAPI,
  deleteIdentityGroup,
  mergeIdentityGroups
} from '../../api';
import UnlabeledFaces from './UnlabeledFaces';
import IdentityList from './IdentityList';
import { useToast } from '@/hooks/use-toast';

export default function IdentityManagement() {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [identityGroups, setIdentityGroups] = useState<IdentityGroup[]>([]);
  const [unlabeledFaces, setUnlabeledFaces] = useState<DetectedFace[]>([]);
  const [selectedFaces, setSelectedFaces] = useState<Record<string, boolean>>({});
  const [isSelectionMode, setIsSelectionMode] = useState<boolean>(false);
  const [selectedIdentity, setSelectedIdentity] = useState<string | null>(null);
  const [selectedIdentityFaces, setSelectedIdentityFaces] = useState<DetectedFace[]>([]);
  const [isLoadingIdentityFaces, setIsLoadingIdentityFaces] = useState<boolean>(false);
  const [viewIdentityDetailsMode, setViewIdentityDetailsMode] = useState<boolean>(false);
  
  // For identity operations
  const [selectedIdentities, setSelectedIdentities] = useState<Record<string, boolean>>({});
  const [isIdentitySelectionMode, setIsIdentitySelectionMode] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [isMerging, setIsMerging] = useState<boolean>(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<boolean>(false);
  const [showMergeConfirm, setShowMergeConfirm] = useState<boolean>(false);
  
  // Current page for unlabeled faces pagination
  const [currentUnlabeledPage, setCurrentUnlabeledPage] = useState<number>(1);
  const [facesPerPage, setFacesPerPage] = useState<number>(60);

  useEffect(() => {
    loadIdentityGroups();
    loadUnlabeledFaces();
  }, []);

  // Reset selection when toggling selection mode
  useEffect(() => {
    if (!isSelectionMode) {
      setSelectedFaces({});
      setSelectedIdentity(null);
    }
  }, [isSelectionMode]);
  
  // Load identity faces when an identity is selected for viewing details
  useEffect(() => {
    if (selectedIdentity && viewIdentityDetailsMode) {
      loadIdentityFaces(selectedIdentity);
    } else {
      setSelectedIdentityFaces([]);
    }
  }, [selectedIdentity, viewIdentityDetailsMode]);
  
  // Function to load all faces for a selected identity
  const loadIdentityFaces = async (identityId: string) => {
    setIsLoadingIdentityFaces(true);
    try {
      // Use a more direct approach since the server doesn't have the specific endpoint
      // Skip trying the dedicated endpoint that we know doesn't exist
      
      // Get identity info first
      let identityInfo: IdentityGroup | undefined;
      
      // Use existing identity groups data if we have it
      identityInfo = identityGroups.find(group => group.id === identityId);
      
      // If we don't have it, try to fetch just this identity
      if (!identityInfo) {
        try {
          const data = await fetchFromAPI(`api/identity-groups/${identityId}`);
          if (data) {
            identityInfo = data;
          }
        } catch (e) {
          console.log(`Could not fetch identity group ${identityId}`, e);
        }
      }
      
      // If we still don't have identity info, we can't proceed
      if (!identityInfo || !identityInfo.face_ids || identityInfo.face_ids.length === 0) {
        console.log(`No face IDs found for identity ${identityId}`);
        setSelectedIdentityFaces([]);
        setIsLoadingIdentityFaces(false);
        return;
      }
      
      // We have identity info, now get faces
      const faceIds = new Set(identityInfo.face_ids);
      console.log(`Found ${faceIds.size} face IDs in identity ${identityId}`);
      let allFaces: DetectedFace[] = [];
      
      // Try to get all faces from a general faces endpoint first
      try {
        const allFacesData = await fetchFromAPI('api/faces');
        if (allFacesData && Array.isArray(allFacesData)) {
          const matchingFaces = allFacesData.filter(face => faceIds.has(face.id));
          if (matchingFaces.length > 0) {
            console.log(`Found ${matchingFaces.length} faces from general faces endpoint`);
            allFaces = matchingFaces;
          }
        } else if (allFacesData && allFacesData.faces && Array.isArray(allFacesData.faces)) {
          const matchingFaces = allFacesData.faces.filter(face => faceIds.has(face.id));
          if (matchingFaces.length > 0) {
            console.log(`Found ${matchingFaces.length} faces from general faces endpoint`);
            allFaces = matchingFaces;
          }
        }
      } catch (e) {
        console.log('General faces endpoint not available');
      }
      
      // If we found faces, we're done
      if (allFaces.length > 0) {
        setSelectedIdentityFaces(allFaces);
        setIsLoadingIdentityFaces(false);
        return;
      }
      
      // If we didn't find faces, try looking in videos
      try {
        // Get list of videos
        const videosData = await fetchFromAPI('api/videos');
        if (videosData && videosData.videos && Array.isArray(videosData.videos)) {
          const videos = videosData.videos;
          console.log(`Found ${videos.length} videos to search for faces`);
          
          // Search through each video for faces
          for (const video of videos.slice(0, 10)) { // Increased to 10 videos
            try {
              const videoData = await fetchFromAPI(`api/videos/${video.id}`);
              if (videoData && videoData.faces && Array.isArray(videoData.faces)) {
                // Filter for faces in this identity group
                const matchingFaces = videoData.faces.filter(face => faceIds.has(face.id));
                console.log(`Found ${matchingFaces.length} matching faces in video ${video.id}`);
                allFaces = [...allFaces, ...matchingFaces];
              }
            } catch (e) {
              console.log(`Error fetching faces for video ${video.id}`, e);
            }
          }
        }
      } catch (e) {
        console.log('Error fetching videos:', e);
      }
      
      // Manual face creation if nothing else worked
      if (allFaces.length === 0) {
        console.log('No faces found through API, creating placeholder faces');
        
        // Create placeholder faces with IDs from the identity group
        const placeholderFaces: DetectedFace[] = Array.from(faceIds).map((faceId, index) => ({
          id: faceId,
          imageUrl: '/placeholder-face.jpg', // This will show as broken image
          timestamp: new Date().toISOString(),
          confidence: 0.9,
          frameNumber: index + 1,
          labeled: true,
          identity_code: identityId
        }));
        
        allFaces = placeholderFaces;
      }
      
      console.log(`Found total of ${allFaces.length} faces for identity ${identityId}`);
      setSelectedIdentityFaces(allFaces);
      setIsLoadingIdentityFaces(false);
      
    } catch (error) {
      console.error(`Error loading faces for identity ${identityId}:`, error);
      setIsLoadingIdentityFaces(false);
      toast({
        title: 'Failed to load identity faces',
        description: 'Could not load faces for this identity group',
        variant: 'destructive'
      });
    } finally {
      setIsLoadingIdentityFaces(false);
    }
  };

  const loadIdentityGroups = async () => {
    try {
      const groups = await fetchIdentityGroups();
      setIdentityGroups(groups);
    } catch (error) {
      console.error('Failed to load identity groups:', error);
      toast({
        title: 'Failed to load identities',
        description: 'Please refresh the page or try again later',
        variant: 'destructive'
      });
    }
  };

  const loadUnlabeledFaces = async () => {
    try {
      // First try to use our API wrapper to fetch unlabeled faces
      const data = await fetchFromAPI('api/unlabeled-faces');
      
      // Check if we got a valid response with faces
      if (data && Array.isArray(data)) {
        console.log(`Found ${data.length} unlabeled faces from API`);
        setUnlabeledFaces(data);
        return;
      }
      
      if (data && data.faces && Array.isArray(data.faces)) {
        console.log(`Found ${data.faces.length} unlabeled faces from API faces property`);
        setUnlabeledFaces(data.faces);
        return;
      }
      
      // Check if we got our custom 404 response
      if (data && data.status === "not_found") {
        console.log("Unlabeled faces endpoint not found, using fallback method");
        // Immediately use fallback method
        await loadAllUnlabeledFaces();
        return;
      }
      
      // If data is empty or invalid, use fallback
      console.log("Received empty or invalid data from API, using fallback method");
      await loadAllUnlabeledFaces();
      
    } catch (error) {
      console.error('Error fetching unlabeled faces:', error);
      // Try a fallback approach to find unlabeled faces
      await loadAllUnlabeledFaces();
    }
  };
  
  // Fallback method to get unlabeled faces from all videos
  const loadAllUnlabeledFaces = async () => {
    try {
      // Get list of videos
      const videosData = await fetchFromAPI('api/videos');
      if (!videosData || !videosData.videos) {
        setUnlabeledFaces([]);
        return;
      }
      
      const videos = videosData.videos;
      let allFaces: DetectedFace[] = [];
      
      // Collect faces from all videos
      for (const video of videos.slice(0, 5)) { // Limit to 5 videos to prevent too many requests
        try {
          const videoData = await fetchFromAPI(`api/videos/${video.id}`);
          if (videoData && videoData.faces && Array.isArray(videoData.faces)) {
            allFaces = [...allFaces, ...videoData.faces.filter(face => !face.labeled)];
          }
        } catch (e) {
          console.log(`Error fetching faces for video ${video.id}`, e);
        }
      }
      
      console.log(`Found ${allFaces.length} unlabeled faces through fallback method`);
      setUnlabeledFaces(allFaces);
      
      if (allFaces.length > 0) {
        toast({
          title: 'Faces found',
          description: `Found ${allFaces.length} unlabeled faces through fallback method`,
        });
      }
    } catch (error) {
      console.error('Error in fallback unlabeled faces loading:', error);
      setUnlabeledFaces([]);
    }
  };

  // Filtered identities based on search
  const filteredIdentities = useMemo(() => {
    if (!searchQuery.trim()) return identityGroups;
    
    return identityGroups.filter(identity => 
      identity.id.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (identity.name && identity.name.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [identityGroups, searchQuery]);

  // Compute paginated unlabeled faces
  const paginatedUnlabeledFaces = useMemo(() => {
    const startIdx = (currentUnlabeledPage - 1) * facesPerPage;
    const endIdx = startIdx + facesPerPage;
    return unlabeledFaces.slice(startIdx, endIdx);
  }, [unlabeledFaces, currentUnlabeledPage, facesPerPage]);

  // Toggle face selection
  const toggleFaceSelection = (faceId: string) => {
    setSelectedFaces(prev => ({
      ...prev,
      [faceId]: !prev[faceId]
    }));
  };

  // Get selected face count
  const selectedFaceCount = useMemo(() => {
    return Object.values(selectedFaces).filter(selected => selected).length;
  }, [selectedFaces]);

  // Create new identity from selected faces
  const createNewIdentity = async () => {
    if (selectedFaceCount === 0) {
      toast({
        title: 'No faces selected',
        description: 'Please select at least one face to create an identity',
        variant: 'destructive'
      });
      return;
    }

    try {
      const selectedFaceIds = Object.entries(selectedFaces)
        .filter(([_, selected]) => selected)
        .map(([faceId]) => faceId);
      
      // If identity is selected, add to existing identity
      if (selectedIdentity) {
        await addFacesToIdentity(selectedIdentity, selectedFaceIds);
        toast({
          title: 'Faces added to identity',
          description: `${selectedFaceIds.length} faces have been added to the identity`
        });
      } else {
        // Create new identity
        const newGroup = await createIdentityGroup(selectedFaceIds);
        toast({
          title: 'New identity created',
          description: `Identity ${newGroup.id} created with ${selectedFaceIds.length} faces`
        });
        setIdentityGroups(prev => [newGroup, ...prev]);
      }
      
      // Reset selection
      setSelectedFaces({});
      setIsSelectionMode(false);
      setSelectedIdentity(null);
      
      // Refresh unlabeled faces
      loadUnlabeledFaces();
    } catch (error) {
      console.error('Failed to create/update identity:', error);
      toast({
        title: 'Operation failed',
        description: 'Could not create or update the identity',
        variant: 'destructive'
      });
    }
  };

  // Handle clicking on an identity - either select for grouping or view details
  const handleIdentityClick = (identityId: string) => {
    console.log(`Identity clicked: ${identityId}, current selection: ${selectedIdentity}, selection mode: ${isSelectionMode}`);
    
    if (isSelectionMode) {
      // In selection mode, selecting identity for grouping
      setSelectedIdentity(identityId === selectedIdentity ? null : identityId);
    } else if (isIdentitySelectionMode) {
      // In identity selection mode for delete/merge operations
      setSelectedIdentities(prev => ({
        ...prev,
        [identityId]: !prev[identityId]
      }));
    } else {
      // In normal mode, view identity details
      setSelectedIdentity(identityId);
      setViewIdentityDetailsMode(true);
      
      // Immediately trigger face loading for this identity
      loadIdentityFaces(identityId);
    }
  };
  
  // Go back to list view from identity details
  const handleBackToList = () => {
    setSelectedIdentity(null);
    setViewIdentityDetailsMode(false);
  };
  
  // Toggle identity selection mode for operations like delete/merge
  const toggleIdentitySelectionMode = () => {
    if (isIdentitySelectionMode) {
      setSelectedIdentities({});
    }
    setIsIdentitySelectionMode(!isIdentitySelectionMode);
  };
  
  // Get count of selected identities
  const getSelectedIdentityCount = () => {
    return Object.values(selectedIdentities).filter(Boolean).length;
  };
  
  // Get array of selected identity IDs
  const getSelectedIdentityIds = () => {
    return Object.entries(selectedIdentities)
      .filter(([_, selected]) => selected)
      .map(([id]) => id);
  };
  
  // Delete selected identities
  const deleteSelectedIdentities = async () => {
    const identityIds = getSelectedIdentityIds();
    if (identityIds.length === 0) {
      toast({
        title: 'No identities selected',
        description: 'Please select at least one identity to delete',
        variant: 'destructive'
      });
      return;
    }
    
    setShowDeleteConfirm(true);
  };
  
  // Perform actual deletion after confirmation
  const confirmDeleteIdentities = async () => {
    const identityIds = getSelectedIdentityIds();
    setIsDeleting(true);
    
    try {
      // Delete each identity in sequence
      for (const id of identityIds) {
        await deleteIdentityGroup(id);
      }
      
      // Update identity list
      const updatedGroups = identityGroups.filter(group => !identityIds.includes(group.id));
      setIdentityGroups(updatedGroups);
      
      toast({
        title: 'Identities deleted',
        description: `Successfully deleted ${identityIds.length} identity groups`,
      });
      
      // Reset selection
      setSelectedIdentities({});
      setIsIdentitySelectionMode(false);
    } catch (error) {
      console.error('Error deleting identities:', error);
      toast({
        title: 'Delete failed',
        description: 'There was an error deleting the identity groups',
        variant: 'destructive'
      });
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };
  
  // Merge selected identities
  const mergeSelectedIdentities = async () => {
    const identityIds = getSelectedIdentityIds();
    if (identityIds.length < 2) {
      toast({
        title: 'Not enough identities selected',
        description: 'Please select at least two identities to merge',
        variant: 'destructive'
      });
      return;
    }
    
    setShowMergeConfirm(true);
  };
  
  // Perform actual merge after confirmation
  const confirmMergeIdentities = async () => {
    const identityIds = getSelectedIdentityIds();
    setIsMerging(true);
    
    try {
      // Sort IDs to find lowest ID
      const sortedIds = [...identityIds].sort((a, b) => {
        // Extract numeric portion for PERSON-XXXX format
        const numA = parseInt(a.split('-')[1]);
        const numB = parseInt(b.split('-')[1]);
        return numA - numB;
      });
      
      const targetId = sortedIds[0];
      const mergedIds = sortedIds.slice(1);
      
      await mergeIdentityGroups(identityIds);
      
      // Update the identity list - remove merged identities and keep target
      const updatedGroups = identityGroups.filter(group => !mergedIds.includes(group.id));
      setIdentityGroups(updatedGroups);
      
      toast({
        title: 'Identities merged',
        description: `Successfully merged ${identityIds.length} identity groups into ${targetId}`,
      });
      
      // Reset selection
      setSelectedIdentities({});
      setIsIdentitySelectionMode(false);
    } catch (error) {
      console.error('Error merging identities:', error);
      toast({
        title: 'Merge failed',
        description: 'There was an error merging the identity groups',
        variant: 'destructive'
      });
    } finally {
      setIsMerging(false);
      setShowMergeConfirm(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Identity Management</h2>
        
        {isSelectionMode ? (
          // Face selection mode controls
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="px-2 py-1">
              {selectedFaceCount} faces selected
            </Badge>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => setIsSelectionMode(false)}
              className="h-9"
            >
              Cancel
            </Button>
            <Button 
              size="sm"
              onClick={createNewIdentity}
              disabled={selectedFaceCount === 0}
              className="h-9"
            >
              {selectedIdentity ? 'Add to Identity' : 'Create New Identity'}
            </Button>
          </div>
        ) : isIdentitySelectionMode ? (
          // Identity selection mode controls
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="px-2 py-1">
              {getSelectedIdentityCount()} identities selected
            </Badge>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => toggleIdentitySelectionMode()}
              className="h-9"
            >
              Cancel
            </Button>
            <Button 
              size="sm"
              variant="destructive"
              onClick={deleteSelectedIdentities}
              disabled={getSelectedIdentityCount() === 0}
              className="h-9"
            >
              Delete Selected
            </Button>
            <Button 
              size="sm"
              onClick={mergeSelectedIdentities}
              disabled={getSelectedIdentityCount() < 2}
              className="h-9"
            >
              Merge to Lowest ID
            </Button>
          </div>
        ) : (
          // Normal mode controls
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              onClick={() => toggleIdentitySelectionMode()}
            >
              Select Identities
            </Button>
            <Button onClick={() => setIsSelectionMode(true)}>
              <UserPlus className="mr-2 h-4 w-4" />
              Group Faces
            </Button>
          </div>
        )}
      </div>

      {/* Confirmation Dialog for Deleting Identities */}
      {showDeleteConfirm && (
        <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Identity Groups</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete {getSelectedIdentityIds().length} identity groups? 
                This action cannot be undone and will remove all associations between these identities and their faces.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
              <AlertDialogAction 
                onClick={confirmDeleteIdentities}
                disabled={isDeleting}
                className="bg-red-600 hover:bg-red-700"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
      
      {/* Confirmation Dialog for Merging Identities */}
      {showMergeConfirm && (
        <AlertDialog open={showMergeConfirm} onOpenChange={setShowMergeConfirm}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Merge Identity Groups</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to merge {getSelectedIdentityIds().length} identity groups? 
                This action will combine all selected identities into the identity with the lowest ID number. 
                This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isMerging}>Cancel</AlertDialogCancel>
              <AlertDialogAction 
                onClick={confirmMergeIdentities}
                disabled={isMerging}
              >
                {isMerging ? 'Merging...' : 'Merge'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
      
      {viewIdentityDetailsMode && selectedIdentity ? (
        // Display identity details view
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>
                {filteredIdentities.find(id => id.id === selectedIdentity)?.name || selectedIdentity}
              </CardTitle>
              <CardDescription>
                Face Details for Identity Group
              </CardDescription>
            </div>
            <Button variant="outline" onClick={handleBackToList}>
              Back to List
            </Button>
          </CardHeader>
          
          <CardContent>
            {isLoadingIdentityFaces ? (
              <div className="flex justify-center py-10">
                <div className="animate-spin h-8 w-8 border-4 border-primary border-r-transparent rounded-full"></div>
              </div>
            ) : selectedIdentityFaces.length === 0 ? (
              <div className="text-center py-10 text-muted-foreground">
                No faces found for this identity. The faces might have been deleted or not properly linked.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">
                    {selectedIdentityFaces.length} Face{selectedIdentityFaces.length !== 1 ? 's' : ''}
                  </h3>
                </div>
                
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                  {selectedIdentityFaces.map(face => (
                    <div key={face.id} className="border rounded-md overflow-hidden">
                      <div className="aspect-square relative">
                        <div className="h-full w-full relative">
                          <img 
                            src={face.imageUrl} 
                            alt="Face" 
                            className="object-cover w-full h-full"
                          />
                        </div>
                        
                        {face.quality_score !== undefined && (
                          <Badge 
                            variant="outline" 
                            className={`absolute bottom-1 right-1 text-xs ${
                              face.quality_score > 80 
                                ? 'bg-green-50 text-green-700 border-green-200' 
                                : face.quality_score > 60
                                  ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                                  : 'bg-red-50 text-red-700 border-red-200'
                            }`}
                          >
                            Q: {face.quality_score}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        // Display normal list view
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle>Identity Groups</CardTitle>
              <CardDescription>Generated identity groups from detected faces</CardDescription>
              
              <div className="mt-4">
                <Label htmlFor="identity-search">Search</Label>
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="identity-search"
                    type="search"
                    placeholder="Search by ID or name..."
                    className="pl-8"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              <IdentityList 
                identities={filteredIdentities}
                selectedIdentity={selectedIdentity}
                isSelectionMode={isSelectionMode}
                isIdentitySelectionMode={isIdentitySelectionMode}
                selectedIdentities={selectedIdentities}
                onSelectIdentity={handleIdentityClick}
              />
            </CardContent>
          </Card>
        
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle>Unlabeled Faces</CardTitle>
              <CardDescription>Faces that have not been assigned to identity groups</CardDescription>
            </CardHeader>
            
            <CardContent>
              <UnlabeledFaces
                faces={paginatedUnlabeledFaces}
                isSelectionMode={isSelectionMode}
                selectedFaces={selectedFaces}
                onToggleSelection={toggleFaceSelection}
                currentPage={currentUnlabeledPage}
                totalPages={Math.ceil(unlabeledFaces.length / facesPerPage)}
                onPageChange={setCurrentUnlabeledPage}
              />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}