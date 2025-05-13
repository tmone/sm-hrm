import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import Image from 'next/image';
import { Users, Search, Tag, UserPlus, ArrowLeft, RefreshCw, Filter, LayoutGrid, List, CheckCheck, Trash2, UserMinus } from 'lucide-react';
import { DetectedFace, IdentityGroup } from '../../types';
import { fetchFacesForVideo, createIdentityGroup, fetchFromAPI, deleteFace, removeFaceFromGroup } from '../../api';

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
  
  // For face dialogs
  const [isDeleteFaceDialogOpen, setIsDeleteFaceDialogOpen] = useState(false);
  const [isRemoveFromGroupDialogOpen, setIsRemoveFromGroupDialogOpen] = useState(false);
  const [faceToDelete, setFaceToDelete] = useState<DetectedFace | null>(null);
  const [faceToRemove, setFaceToRemove] = useState<DetectedFace | null>(null);
  
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
      if (!face.identity_code) return false;
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
      return { 
        individuals: filteredFaces,
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
    
    // Groups are only included when not filtering
    return {
      individuals,
      groups: searchQuery ? 
        // When searching, only include groups that match the search
        groupedFaces.filter(g => g.identityCode.toLowerCase().includes(searchQuery.toLowerCase())) : 
        groupedFaces
    };
  }, [filteredFaces, groupedFaces, filterLabeled, searchQuery]);
  
  // Pagination with individuals and groups combined
  const paginatedContent = React.useMemo(() => {
    // For display purposes, we want to show individuals first, then grouped cards at the end
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
  
  // Option to navigate to identity page
  const navigateToIdentity = (identityCode: string) => {
    // Close the dialog first
    setIsIdentityDialogOpen(false);
    
    // Navigate to identity management page
    router.push(`/facial-recognition?view=identity&id=${identityCode}`);
  };
  
  // Handle delete face (permanent deletion)
  const handleDeleteFace = async () => {
    if (!faceToDelete) return;
    
    try {
      // Call the API to delete the face
      await deleteFace(videoId, faceToDelete.id);
      
      // Update local state to remove the face
      setFaces(prevFaces => prevFaces.filter(face => face.id !== faceToDelete.id));
      
      // Update identity faces if open
      if (isIdentityDialogOpen && selectedIdentity) {
        setIdentityFaces(prevFaces => prevFaces.filter(face => face.id !== faceToDelete?.id));
      }
      
      // Show success message
      toast({
        title: "Face deleted",
        description: "The face has been permanently deleted",
      });
      
      // Close the dialog
      setIsDeleteFaceDialogOpen(false);
      setFaceToDelete(null);
    } catch (error) {
      console.error('Error deleting face:', error);
      toast({
        title: "Failed to delete face",
        description: "An error occurred while trying to delete the face",
        variant: "destructive"
      });
    }
  };
  
  // Handle removing face from group (keeps face but removes from group)
  const handleRemoveFaceFromGroup = async () => {
    if (!faceToRemove || !faceToRemove.identity_code) return;
    
    try {
      // Call the API to remove the face from the group
      await removeFaceFromGroup(faceToRemove.identity_code, faceToRemove.id);
      
      // Update local state to remove the identity_code
      setFaces(prevFaces => prevFaces.map(face => {
        if (face.id === faceToRemove.id) {
          // Create a new face object without the identity_code
          const { identity_code, ...restFace } = face;
          return restFace;
        }
        return face;
      }));
      
      // Update identity faces if open
      if (isIdentityDialogOpen && selectedIdentity) {
        setIdentityFaces(prevFaces => prevFaces.filter(face => face.id !== faceToRemove?.id));
      }
      
      // Show success message
      toast({
        title: "Face removed from group",
        description: "The face has been removed from the group and is now an individual face",
      });
      
      // Close the dialog
      setIsRemoveFromGroupDialogOpen(false);
      setFaceToRemove(null);
    } catch (error) {
      console.error('Error removing face from group:', error);
      toast({
        title: "Failed to remove from group",
        description: "An error occurred while trying to remove the face from the group",
        variant: "destructive"
      });
    }
  };
  
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

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (e) {
      return timestamp;
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
          <CardHeader className="pb-3 sticky top-0 z-10 bg-background border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Face Management</CardTitle>
                <CardDescription>
                  {filteredFaces.length} face{filteredFaces.length !== 1 ? 's' : ''} found
                </CardDescription>
              </div>
              
              <div className="flex items-center gap-2">
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
                No faces match your filters.
              </div>
            ) : viewMode === 'grid' ? (
              // Grid View
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
                {paginatedContent.map((item, index) => {
                  // Check if this is a group card
                  if ('type' in item && item.type === 'group') {
                    const group = item.data;
                    return (
                      <div 
                        key={`group-${group.identityCode}`} 
                        className="border rounded-md overflow-hidden bg-primary/5 cursor-pointer hover:bg-primary/10 transition-colors"
                        onClick={() => viewIdentityFaces(group.identityCode)}
                      >
                        <div className="aspect-square relative">
                          {/* Show the representative face of the group */}
                          <Image
                            src={group.representativeFace.imageUrl}
                            alt="Group Representative"
                            fill
                            className="object-cover"
                          />
                          
                          {/* Group badge */}
                          <div className="absolute inset-0 bg-black/30 flex flex-col items-center justify-center">
                            <Badge 
                              variant="outline" 
                              className="px-3 py-1.5 text-lg font-semibold bg-white text-primary border-primary mb-2"
                            >
                              Group
                            </Badge>
                            <div className="text-white font-bold text-lg">{group.identityCode}</div>
                            <div className="text-white/90 text-sm mt-1">{group.faceCount} faces</div>
                          </div>
                          
                          {/* Quality indicator */}
                          {group.representativeFace.quality_score !== undefined && (
                            <Badge 
                              variant="outline" 
                              className="absolute bottom-1 right-1 text-xs bg-blue-500/70 text-white border-none"
                            >
                              Best Q: {group.representativeFace.quality_score}
                            </Badge>
                          )}
                        </div>
                        
                        <div className="p-2 text-center font-medium bg-primary/10 text-primary">
                          Click to view all faces
                        </div>
                      </div>
                    );
                  }
                  
                  // Regular face card (individual)
                  const face = item as DetectedFace;
                  return (
                    <div 
                      key={face.id} 
                      className={`border rounded-md overflow-hidden ${
                        selectedFaces[face.id] ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => toggleFaceSelection(face.id)}
                    >
                      <div className="aspect-square relative">
                        <Image
                          src={face.imageUrl}
                          alt="Face"
                          fill
                          className="object-cover"
                        />
                        
                        <div className="absolute top-1 right-1 flex gap-1">
                          <Button
                            size="icon"
                            variant="destructive"
                            className="h-6 w-6 rounded-full bg-red-500/70 hover:bg-red-600/90"
                            onClick={(e) => {
                              e.stopPropagation();
                              promptDeleteFace(face);
                            }}
                          >
                            <Trash2 className="h-3 w-3 text-white" />
                          </Button>
                          <Checkbox 
                            checked={selectedFaces[face.id] || false}
                            className="h-5 w-5 bg-white/80"
                            onClick={(e) => e.stopPropagation()}
                            onCheckedChange={() => toggleFaceSelection(face.id)}
                          />
                        </div>
                        
                        {face.identity_code && (
                          <Badge 
                            variant="outline" 
                            className="absolute bottom-1 left-1 bg-black/50 text-white border-none"
                          >
                            {face.identity_code}
                          </Badge>
                        )}
                        
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
                  );
                })}
              </div>
            ) : (
              // List View
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
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
                          className={selectedFaces[face.id] ? 'bg-primary/5' : ''}
                        >
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Button
                                size="icon"
                                variant="destructive"
                                className="h-6 w-6 rounded-full"
                                onClick={() => promptDeleteFace(face)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                              <Checkbox 
                                checked={selectedFaces[face.id] || false}
                                onCheckedChange={() => toggleFaceSelection(face.id)}
                              />
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
      
      {/* Group Confirmation Dialog */}
      <Dialog open={isGroupDialogOpen} onOpenChange={setIsGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Identity Group</DialogTitle>
            <DialogDescription>
              You are about to group {selectedFaceCount} face{selectedFaceCount !== 1 ? 's' : ''} into a single identity.
              This will assign {selectedFaceCount === 1 ? 'it' : 'them all'} the same PERSON-XXXX identifier.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <h4 className="font-medium mb-2">Selected Faces:</h4>
            <div className="grid grid-cols-4 gap-2 max-h-60 overflow-y-auto p-2 border rounded-md">
              {Object.entries(selectedFaces)
                .filter(([_, selected]) => selected)
                .map(([faceId]) => {
                  const face = faces.find(f => f.id === faceId);
                  if (!face) return null;
                  
                  return (
                    <div key={faceId} className="relative h-20 rounded-md overflow-hidden">
                      <Image
                        src={face.imageUrl}
                        alt="Selected face"
                        fill
                        className="object-cover"
                      />
                    </div>
                  );
                })}
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsGroupDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={groupSelectedFaces}>
              <CheckCheck className="mr-2 h-4 w-4" />
              Confirm Grouping
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Identity Faces Dialog */}
      <Dialog open={isIdentityDialogOpen} onOpenChange={setIsIdentityDialogOpen}>
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
            {isLoadingIdentityFaces ? (
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
                        <Image
                          src={face.imageUrl}
                          alt="Face"
                          fill
                          className="object-cover"
                        />
                        
                        <Button
                          size="icon"
                          variant="destructive"
                          className="absolute top-1 right-1 h-6 w-6 rounded-full bg-blue-500/70 hover:bg-blue-600/90"
                          onClick={() => promptRemoveFromGroup(face)}
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
                    onClick={() => navigateToIdentity(selectedIdentity!)}
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
              onClick={() => setIsIdentityDialogOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Delete Face Confirmation Dialog */}
      <AlertDialog open={isDeleteFaceDialogOpen} onOpenChange={setIsDeleteFaceDialogOpen}>
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
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteFace}
              className="bg-red-600 hover:bg-red-700"
            >
              Permanently Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Remove Face from Group Dialog */}
      <AlertDialog open={isRemoveFromGroupDialogOpen} onOpenChange={setIsRemoveFromGroupDialogOpen}>
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
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleRemoveFaceFromGroup}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Remove from Group
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}