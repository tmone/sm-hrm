// Utility function to fetch data from Python backend
export async function fetchFromPythonBackend(endpoint: string) {
  try {
    const pythonBackendUrl = process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || "http://127.0.0.1:7860";
    const response = await fetch(`${pythonBackendUrl}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch data: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error fetching from Python backend:", error);
    throw error;
  }
}