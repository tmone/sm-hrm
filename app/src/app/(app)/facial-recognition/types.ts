export interface RegisteredFace {
  id: string;
  employeeName: string;
  employeeId: string;
  imageUrl?: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  registeredDate: string;
}

export interface UploadedVideo {
  id: string;
  filename: string;
  file_url: string;
  status: string;
  uploaded_at: string;
  processing_status?: string;
  faces?: DetectedFace[];
  task_id?: string;
  ui_processing?: boolean; // UI state to show processing status
  is_deleted?: boolean;    // Flag to indicate if video is deleted/archived
}

export interface ProcessingTask {
  task_id: string;
  video_id: string;
  status: string;
  progress: number; // Making this required to match backend validation
  face_count?: number;
  error?: string;
  retry_count?: number; // Added for our retry mechanism
  update_retry_count?: number; // Added for our retry mechanism
  last_updated?: string; // Added for tracking
}

export interface DetectedFace {
  id: string;
  imageUrl: string;
  timestamp: string;
  confidence: number;
  frameNumber: number;
  labeled: boolean;
  employee_id?: string;
  employeeName?: string;
  group_id?: string;
  landmarks?: {x: number, y: number}[];
  quality_score?: number; // 0-100 quality score for the face
  is_best_face?: boolean; // Whether this is the best quality face in its group
  identity_code?: string; // PERSON-XXXX code for manual identity grouping
  selected?: boolean;     // Whether face is selected for manual grouping
}

export interface FaceGroup {
  id: string;
  face_ids: string[];
  similarity_score: number;
  created: string;
  last_updated: string;
  labeled: boolean;
  label?: string;
  employee_id?: string;
  representative_face?: DetectedFace; // Representative face for the group
  best_face_id?: string;              // ID of the highest quality face in the group
  best_face?: DetectedFace;           // Reference to the best quality face
  avg_quality_score?: number;         // Average quality score of faces in the group
}

export interface IdentityGroup {
  id: string;                // PERSON-XXXX format
  face_ids: string[];        // IDs of faces in this identity
  name?: string;             // Optional human-readable name
  created: string;           // Creation timestamp
  video_ids: string[];       // Videos these faces appear in
  primary_face_id?: string;  // ID of the primary face (usually best quality)
  employee_id?: string;      // Employee ID if assigned
}

export interface Employee {
  id: string;
  name: string;
  department: string;
  position: string;
  email: string;
  phone: string;
  status: string;
  faceStatus?: 'Pending' | 'Approved' | 'Rejected' | null;
  faceRegisteredDate?: string | null;
  faceImageUrl?: string | null;
}

// Custom error types for better error handling
export class APIError extends Error {
  statusCode: number;
  endpoint: string;
  
  constructor(message: string, statusCode: number, endpoint: string) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.endpoint = endpoint;
  }
}

export class NotFoundError extends APIError {
  constructor(endpoint: string) {
    super(`Resource not found (404): ${endpoint}`, 404, endpoint);
    this.name = 'NotFoundError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}