import { NextRequest, NextResponse } from 'next/server';
import { fetchFromAPI } from '@/app/(app)/facial-recognition/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Call the Python API to start training
    const response = await fetchFromAPI('api/training/start', {
      method: 'POST',
      body: JSON.stringify(body)
    });
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error starting training:', error);
    return NextResponse.json({ 
      error: error instanceof Error ? error.message : 'Failed to start training' 
    }, { status: 500 });
  }
}