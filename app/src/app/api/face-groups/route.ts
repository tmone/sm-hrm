import { NextRequest, NextResponse } from 'next/server';
import { fetchFromAPI } from '@/app/(app)/facial-recognition/api';

export async function GET(request: NextRequest) {
  try {
    // Call the Python API to get face groups
    const data = await fetchFromAPI('api/face-groups');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching face groups:', error);
    return NextResponse.json({ 
      groups: [], 
      error: error instanceof Error ? error.message : 'Failed to fetch face groups' 
    }, { status: 500 });
  }
}