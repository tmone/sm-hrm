import { NextRequest, NextResponse } from 'next/server';
import { fetchFromAPI } from '@/app/(app)/facial-recognition/api';

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const { jobId } = params;
    
    // Call the Python API to get training status
    const response = await fetchFromAPI(`api/training/status/${jobId}`);
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error getting training status:', error);
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Failed to get training status' 
    }, { status: 500 });
  }
}