import { fetchFromPythonBackend } from '../python-bridge';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Fetch data from Python backend
    const data = await fetchFromPythonBackend('/api/hello');
    
    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in Python demo API route:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with Python backend' },
      { status: 500 }
    );
  }
}