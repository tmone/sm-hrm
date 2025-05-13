'use client';

import React from 'react';
import VideoLabeling from '../../components/VideoLabeling';

// This is the client component wrapper that receives props from the server component
export default function VideoLabelingWrapper({ videoId }: { videoId: string }) {
  return <VideoLabeling videoId={videoId} />;
}