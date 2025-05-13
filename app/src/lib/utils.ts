import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { API_URL } from "./constants"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Utility function to create a properly formatted API URL
 * Handles cases where endpoint might already include 'api/' prefix
 * 
 * @param endpoint The API endpoint path (with or without 'api/' prefix)
 * @returns A properly formatted URL for the API endpoint
 */
export function createApiUrl(endpoint: string): string {
  // If endpoint already starts with 'api/', just add leading slash
  if (endpoint.startsWith('api/')) {
    return `/${endpoint}`
  } 
  
  // Otherwise, combine API_URL with endpoint, ensuring no double slashes
  return `${API_URL}/${endpoint.startsWith('/') ? endpoint.substring(1) : endpoint}`
}

/**
 * Fetch data from the API with proper error handling
 * 
 * @param endpoint The API endpoint to fetch from
 * @param options Optional fetch options
 * @returns The JSON response from the API
 */
export async function fetchFromApi<T = any>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  try {
    const url = createApiUrl(endpoint)
    
    // Log the URL being fetched (helpful for debugging)
    console.debug(`Fetching from: ${url}`)
    
    const defaultOptions: RequestInit = {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
      },
      credentials: 'same-origin'
    }

    // Merge headers correctly
    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...(options.headers || {})
      }
    }
    
    const response = await fetch(url, mergedOptions)

    if (!response.ok) {
      const errorMessage = `API response error: ${response.status} ${response.statusText}`
      console.error(errorMessage)
      
      // Try to extract error details if available
      try {
        const errorData = await response.json()
        if (errorData.detail) {
          throw new Error(`${errorMessage}: ${errorData.detail}`)
        }
      } catch (parseError) {
        // If we can't parse the error response, just throw the original error
      }
      
      throw new Error(errorMessage)
    }

    return await response.json()
  } catch (error) {
    console.error(`Error fetching data from ${endpoint}:`, error)
    throw error
  }
}
