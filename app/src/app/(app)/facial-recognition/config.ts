/**
 * Configuration for the facial recognition API
 * These values can be overridden by environment variables
 */

// API configuration
export const API_CONFIG = {
  // Base URL for API requests - should not have trailing slash
  // Try using an empty base URL for relative path routing
  baseUrl: '',
  
  // Whether to include credentials in cross-origin requests
  withCredentials: true,
  
  // CORS mode for API requests - set to cors for cross-origin requests
  corsMode: 'cors' as RequestMode
};