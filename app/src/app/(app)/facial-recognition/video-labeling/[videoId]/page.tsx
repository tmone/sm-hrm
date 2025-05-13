'use client';

import React, { use } from 'react';
import VideoLabelingWrapper from './VideoLabelingWrapper';

// Using React.use() to unwrap the params promise as recommended by Next.js
export default function VideoLabelingPage({ params }: { params: { videoId: string } }) {
  // Properly unwrap the params object using React.use()
  const unwrappedParams = use(params);
  const videoId = unwrappedParams.videoId;
  
  return <VideoLabelingWrapper videoId={videoId} />;
}