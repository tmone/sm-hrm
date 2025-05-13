// This is a server component (no 'use client')
import React from 'react';
import VideoLabelingWrapper from './VideoLabelingWrapper';

// Server components can handle params correctly
export default function VideoLabelingPage({ params }: { params: { videoId: string } }) {
  // Extract parameter in the server component
  const videoId = params.videoId;
  
  // Pass it to a client component wrapper
  return <VideoLabelingWrapper videoId={videoId} />;
}