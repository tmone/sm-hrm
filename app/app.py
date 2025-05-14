import gradio as gr
import os
import json
import tempfile
import shutil
import io
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form, BackgroundTasks, Body
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.FileHandler("server.log"),
                            logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Import database and models
from db.database import get_db
from db import models, auth
from db.init_db import init_db
from db.face_detection import face_detector
from db.face_cache import face_cache
from db.uploads import upload_manager
from db.background_processor import background_processor
from db.dashboard import dashboard_manager
from db.employees import employees_manager
from db.attendance import attendance_manager
from db.leave import leave_manager
from db.face_landmarks import face_landmark_detector
from db.face_groups import face_group_manager
from db.parallel_face_processor import parallel_face_processor
from db.cleanup import cleanup_manager
from db.identity_groups import identity_group_manager
from db.users import UserManager
from db.roles import RoleManager
from db.user_settings import UserSettingsManager

# Initialize the database
init_db()

# Pydantic models for API requests and responses
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str
    is_admin: Optional[bool] = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserPasswordUpdate(BaseModel):
    new_password: str
    
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    roles: List = []

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    
    class Config:
        from_attributes = True

class RoleWithUserCount(RoleResponse):
    user_count: int

class UserSettingsModel(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = False
    leave_alerts: bool = True
    
    class Config:
        from_attributes = True

class Employee(BaseModel):
    id: Optional[int] = None
    employee_id: str
    name: str
    position: str
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True

# Initialize FastAPI
app = FastAPI(
    title="StepmediaHRM",
    description="Human Resource Management System API",
    version="0.1.0",
)

# Configure server to allow larger file uploads (2GB)
app.state.MAX_FILE_SIZE = 2048 * 1024 * 1024  # 2048MB (2GB) in bytes

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9002", "http://127.0.0.1:9002", "*"],  # Add explicit origins + wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type", "Authorization"]
)

# Authentication endpoints
@app.post("/api/token", response_model=LoginResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token for authentication.
    Uses OAuth2 password flow.
    """
    user = auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# User management
@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create a new user (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    # Check if username exists
    existing_user = user_manager.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    existing_email = user_manager.get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = user_manager.create_user(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password=user.password,
        is_admin=user.is_admin or False
    )
    
    return new_user

@app.get("/api/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(auth.get_current_user)):
    """Get all users (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    users = user_manager.get_all_users()
    return users

@app.get("/api/users/search", response_model=List[UserResponse])
async def search_users(q: str, current_user: dict = Depends(auth.get_current_user)):
    """Search users by name, email, or username (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    users = user_manager.search_users(q)
    return users

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Get a user by ID (requires admin privileges or be the same user)"""
    if not current_user.get("is_admin", False) and str(current_user.get("id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(auth.get_current_user)):
    """Get the current user's information"""
    return current_user

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update a user's details (requires admin privileges or be the same user)"""
    if not current_user.get("is_admin", False) and str(current_user.get("id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    # Only admins can change admin status
    if not current_user.get("is_admin", False) and user.is_admin is not None:
        raise HTTPException(status_code=403, detail="Not authorized to change admin status")
    
    updated_user = user_manager.update_user(
        user_id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin
    )
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

@app.put("/api/users/{user_id}/password")
async def update_user_password(user_id: int, password_data: UserPasswordUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update a user's password (requires admin privileges or be the same user)"""
    if not current_user.get("is_admin", False) and str(current_user.get("id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    updated_user = user_manager.update_password(user_id, password_data.new_password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password updated successfully"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a user (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Don't allow deleting yourself
    if str(current_user.get("id")) == str(user_id):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    success = user_manager.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Face recognition endpoints
@app.get("/api/employees/with-facial-data")
async def list_employees_with_facial_data(db: Session = Depends(get_db),
                                         current_user: dict = Depends(auth.get_current_user_optional)):
    """
    List all employees who have facial data registered.
    This is used by the attendance system to show which employees
    can be identified by face recognition.
    """
    # Get employees with facial data
    employees_with_faces = db.query(models.Employee)\
        .join(models.FacialData)\
        .filter(models.FacialData.is_approved == True)\
        .all()
    
    # Format response
    return {
        "employees": [
            {
                "id": emp.id,
                "employee_id": emp.employee_id,
                "name": emp.name,
                "position": emp.position,
                "department": emp.department,
                "image_path": emp.facial_data.image_path if emp.facial_data else None
            }
            for emp in employees_with_faces
        ]
    }

@app.post("/api/register-face/{employee_id}")
async def register_face(employee_id: int, 
                        face_image: UploadFile = File(...),
                        db: Session = Depends(get_db),
                        current_user: dict = Depends(auth.get_current_user_optional)):
    """
    Register a face for an employee.
    This creates or updates the facial data for the employee.
    """
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    # Process the uploaded image and create face encoding
    try:
        # Create a temporary file to save the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(await face_image.read())
            temp_file_path = temp_file.name
        
        # Use our face detector to encode the face
        face_encoding = face_detector.encode_face(temp_file_path)
        
        if not face_encoding:
            os.unlink(temp_file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face found in the uploaded image"
            )
        
        # Create a permanent path for the image
        perm_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "faces")
        os.makedirs(perm_dir, exist_ok=True)
        
        perm_file = os.path.join(perm_dir, f"employee_{employee_id}.jpg")
        shutil.copyfile(temp_file_path, perm_file)
        
        # Create relative URL for the image
        image_url = f"/static/faces/employee_{employee_id}.jpg"
        
        # Convert face encoding to JSON-compatible format
        face_encoding_json = json.dumps(face_encoding.tolist())
        
        # Check if employee already has facial data
        existing_data = db.query(models.FacialData).filter(models.FacialData.employee_id == employee_id).first()
        
        if existing_data:
            # Update existing data
            existing_data.face_encoding = face_encoding_json
            existing_data.image_path = image_url
            existing_data.is_approved = True
            existing_data.updated_at = datetime.now()
        else:
            # Create new facial data
            facial_data = models.FacialData(
                employee_id=employee_id,
                face_encoding=face_encoding_json,
                image_path=image_url,
                is_approved=True
            )
            db.add(facial_data)
        
        db.commit()
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return {
            "message": f"Face registered for employee {employee.name}",
            "employee_id": employee_id,
            "image_url": image_url
        }
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        print(f"Error registering face: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering face: {str(e)}"
        )

@app.post("/api/process-video")
async def process_video(video_file: UploadFile = File(...),
                      session_id: str = Form(None),
                      current_user: dict = Depends(auth.get_current_user_optional)):
    """
    Process a video file to detect and extract faces.
    Returns a list of detected faces with timestamps.
    """
    # Generate a session ID if not provided
    if not session_id:
        session_id = face_cache.create_session()
    
    try:
        # Create a temporary file to save the uploaded video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            # Use a buffer size of 64KB for efficient copying
            buffer_size = 64 * 1024  # 64KB
            
            # Read and write in chunks to handle large files
            while chunk := await video_file.read(buffer_size):
                temp_file.write(chunk)
                
            temp_file_path = temp_file.name
        
        print(f"Saved uploaded video to temporary file: {temp_file_path}")
        
        # Process the video with our face detector using a time-based window
        detected_faces = face_detector.process_video(temp_file_path, time_window_ms=100)
        
        print(f"Detected {len(detected_faces)} faces in video")
        
        # Store the detected faces in the session
        face_cache.add_faces(session_id, detected_faces)
        
        # Return the detected faces
        return {
            "session_id": session_id,
            "faces": [
                {
                    "id": face["id"],
                    "imageUrl": face["imageUrl"],
                    "timestamp": face["metadata"].get("timestamp", "00:00:00"),
                    "assigned": face["assigned"],
                    "assignedTo": face.get("assignedTo", None),
                    "confidence": face["metadata"].get("confidence", 1.0)
                } for face in detected_faces
            ]
        }
    
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        # Try to return any faces that were detected before the error
        session = face_cache.get_session(session_id)
        cached_faces = []
        
        if session and 'faces' in session:
            cached_faces = [{
                'id': face['id'],
                'imageUrl': face['imageUrl'],
                'timestamp': face['metadata'].get('timestamp', '00:00:00'),
                'assigned': face['assigned'],
                'assignedTo': face.get('assignedTo', None),
                'confidence': face['metadata'].get('confidence', 1.0)
            } for face in session['faces']]
            
        if cached_faces:
            return {
                "message": f"Partial processing of video due to error: {str(e)}",
                "status": "partial_success",
                "error": str(e),
                "session_id": session_id,
                "faces": cached_faces
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing video: {str(e)}"
            )

# Assign detected face to an employee
@app.post("/api/assign-face")
async def assign_face(face_id: str = Form(...),
                     employee_id: str = Form(...),
                     session_id: str = Form(...),
                     employee_name: str = Form(None),
                     db: Session = Depends(get_db)):
    """
    Assign a detected face to an employee.
    This would typically update a database record.
    """
    try:
        # Verify session exists
        session = face_cache.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
            
        # If employee name not provided, try to get it from the database
        if not employee_name:
            # In a real app, you would query the employee table
            # For now, we'll use a mock name
            employee_name = f"Employee {employee_id}"
            
        # Assign the face in the cache
        success = face_cache.assign_face(session_id, face_id, employee_id, employee_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Face not found in session: {face_id}"
            )
        
        return {
            "message": f"Successfully assigned face {face_id} to employee {employee_id}",
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error assigning face: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning face: {str(e)}"
        )

# Gradio interface for facial recognition demo
with gr.Blocks() as demo:
    gr.Markdown("# StepmediaHRM Facial Recognition")
    with gr.Row():
        input_image = gr.Image(type="pil", label="Upload Face")
        output_text = gr.Textbox(label="Recognition Result")

    submit_btn = gr.Button("Recognize")

    def recognize_face(image):
        # Placeholder for actual facial recognition logic
        if image is None:
            return "No image provided"
        return "Employee recognized: John Doe"

    submit_btn.click(fn=recognize_face, inputs=input_image, outputs=output_text)

# Models for video processing
class VideoUploadResponse(BaseModel):
    upload_id: str
    filename: str
    file_url: str
    status: str
    uploaded_at: str

class VideoProcessingResponse(BaseModel):
    task_id: str
    video_id: str
    status: str
    progress: float
    error: Optional[str] = None
    face_count: Optional[int] = None
    recovered: Optional[bool] = None

# Video upload and processing endpoints
@app.post("/api/videos/upload", response_model=VideoUploadResponse)
async def upload_video(
    video_file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Upload a video file for face detection processing"""
    
    # Check file size against server limit (500MB)
    file_size = 0
    content = await video_file.read(1024)  # Read first chunk to check if file exists
    file_size += len(content)
    
    # Seek back to beginning of file
    await video_file.seek(0)
    
    # Get max file size from app state
    max_file_size = getattr(app.state, "MAX_FILE_SIZE", 2048 * 1024 * 1024)  # Default to 2GB
    
    # Create metadata with user info and description
    metadata = {
        "description": description,
        "uploaded_by": current_user["id"] if current_user else None,
        "uploaded_by_name": current_user["full_name"] if current_user else "Anonymous"
    }
    
    # Save the video using the upload manager
    try:
        # Use a more efficient approach for streaming the upload
        video_record = upload_manager.save_video(video_file.file, video_file.filename, metadata)
        
        return {
            "upload_id": video_record["id"],
            "filename": video_record["original_filename"],
            "file_url": video_record["file_url"],
            "status": video_record["processing_status"],
            "uploaded_at": video_record["uploaded_at"]
        }
    except Exception as e:
        print(f"Error uploading video: {str(e)}")
        # Check if it's a file size error coming from the client
        if "File size exceeds" in str(e):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({max_file_size/(1024*1024):.0f}MB)"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading video: {str(e)}"
        )

@app.post("/api/videos/{video_id}/process", response_model=VideoProcessingResponse)
async def process_video_background(
    video_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Start processing a previously uploaded video for face/human detection"""

    # Get the video record
    video = upload_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Add the video to the processing queue
    try:
        task_id = background_processor.add_video_processing_task(video_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return the task ID
    return {
        "task_id": task_id,
        "video_id": video_id,
        "status": "queued",
        "progress": 0
    }

@app.post("/api/videos/{video_id}/recover", response_model=VideoProcessingResponse)
async def recover_video_processing(
    video_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Attempt to recover a failed video processing job"""

    # Get the video record
    video = upload_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Try to recover the processing
    try:
        task_id = f"task_{video_id}"
        success = background_processor.recover_video_processing(video_id, task_id)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to recover video {video_id}. No faces could be salvaged."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return the task ID with recovery status
    return {
        "task_id": task_id,
        "video_id": video_id,
        "status": "completed",
        "progress": 100,
        "recovered": True
    }

@app.get("/api/tasks/{task_id}", response_model=VideoProcessingResponse)
async def get_task_status(task_id: str,
                        current_user: dict = Depends(auth.get_current_user_optional)):
    """Get the status of a background processing task"""

    # Get the task status
    task_status = background_processor.get_task_status(task_id)
    if not task_status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Ensure all required fields are present
    if "video_id" not in task_status:
        # Try to extract video_id from task_id (often follows format "task_<video_id>")
        if task_id.startswith("task_"):
            task_status["video_id"] = task_id[5:]  # Remove "task_" prefix
        else:
            task_status["video_id"] = ""
    
    if "progress" not in task_status:
        task_status["progress"] = 0.0
    
    # Make sure all fields from VideoProcessingResponse are present
    # Optional fields get default values if not specified
    return {
        "task_id": task_status.get("task_id", task_id),
        "video_id": task_status.get("video_id", ""),
        "status": task_status.get("status", "unknown"),
        "progress": task_status.get("progress", 0.0),
        "error": task_status.get("error"),
        "face_count": task_status.get("face_count"),
        "recovered": task_status.get("recovered")
    }

@app.get("/api/videos")
async def list_videos(status: Optional[str] = None,
                    include_deleted: bool = False,
                    current_user: dict = Depends(auth.get_current_user_optional)):
    """
    List all uploaded videos, optionally filtered by status

    Args:
        status: Filter by processing status
        include_deleted: If True, include videos marked as deleted
    """
    try:
        # Log for debugging
        logger.info(f"Fetching videos with status={status}, include_deleted={include_deleted}")
        
        # Get all videos with enhanced error handling
        videos = upload_manager.get_all_videos(status, include_deleted)
        
        # Log result
        logger.info(f"Found {len(videos)} videos")
        
        # Additional verification for videos and their faces
        validated_videos = []
        
        for video in videos:
            if not isinstance(video, dict):
                logger.warning(f"Skipping invalid video record (not a dict): {type(video)}")
                continue
                
            # Ensure required fields exist with defaults
            video_id = video.get("id", str(uuid.uuid4()))
            video.setdefault("id", video_id)
            video.setdefault("processing_status", "unknown")
            video.setdefault("original_filename", "unknown.mp4")
            video.setdefault("uploaded_at", datetime.now().isoformat())
            video.setdefault("is_deleted", False)
            
            # Validate faces
            if "faces" not in video or not isinstance(video["faces"], list):
                logger.warning(f"Video {video_id} missing or invalid 'faces' field, setting to empty array")
                video["faces"] = []
            
            # Ensure each face has the required properties
            if video["faces"]:
                validated_faces = []
                for face in video["faces"]:
                    if not isinstance(face, dict):
                        logger.warning(f"Skipping invalid face in video {video_id} (not a dict)")
                        continue
                        
                    # Ensure face has an ID
                    if "id" not in face:
                        face["id"] = str(uuid.uuid4())
                        logger.warning(f"Added missing id to face in video {video_id}")
                    
                    # Ensure face has an imageUrl (critical for frontend)
                    if "imageUrl" not in face:
                        if "face_path" in face:
                            # Derive imageUrl from face_path
                            face_filename = os.path.basename(face["face_path"])
                            face["imageUrl"] = f"/static/faces/{face_filename}"
                            logger.info(f"Added derived imageUrl for face {face['id']} in video {video_id}")
                        else:
                            # Use placeholder if no path available
                            face["imageUrl"] = "/static/placeholder-face.jpg"
                            logger.warning(f"Added placeholder imageUrl for face {face['id']} in video {video_id}")
                    
                    validated_faces.append(face)
                
                video["faces"] = validated_faces
            
            validated_videos.append(video)
        
        # Return the validated list
        return {"videos": validated_videos}
    except Exception as e:
        # Log the error with full traceback for diagnosis
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error listing videos: {str(e)}\n{error_details}")
        
        # Try to return a partial result with more error details
        try:
            # Make a second attempt with more defensive approach
            logger.info("Attempting to retrieve videos with fallback method")
            
            # Get a fresh instance of upload_manager if needed
            try:
                from db.uploads import UploadManager
                fallback_manager = UploadManager()
                partial_videos = fallback_manager.get_all_videos(status, include_deleted) or []
                logger.info(f"Fallback retrieved {len(partial_videos)} videos")
            except Exception as fallback_error:
                logger.error(f"Fallback retrieval failed: {str(fallback_error)}")
                partial_videos = []
            
            # Return partial results with detailed error information
            return {
                "videos": partial_videos,
                "partial_results": True,
                "error": {
                    "message": str(e),
                    "type": e.__class__.__name__,
                    "code": "VIDEO_LIST_ERROR"
                }
            }
        except Exception as fallback_e:
            # If even the fallback fails, provide detailed error
            logger.critical(f"Complete failure in video listing API: {str(fallback_e)}")
            
            # Raise HTTP exception with more details
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": f"Error listing videos: {str(e)}",
                    "type": e.__class__.__name__,
                    "fallback_error": str(fallback_e),
                    "code": "VIDEO_LIST_CRITICAL_ERROR"
                }
            )

@app.get("/api/videos/{video_id}")
async def get_video(video_id: str,
                  current_user: dict = Depends(auth.get_current_user_optional)):
    """Get details for a specific video"""

    # Get the video record
    video = upload_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Return the video details
    return video

@app.delete("/api/videos/{video_id}")
async def delete_video(video_id: str,
                     current_user: dict = Depends(auth.get_current_user_optional)):
    """Delete a video file and its record"""

    # Delete the video
    success = upload_manager.delete_video(video_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Return success response
    return {"status": "success", "message": f"Video {video_id} deleted successfully"}

@app.post("/api/faces/{face_id}/label")
async def label_face(face_id: str,
                    employee_id: str = Form(...),
                    video_id: str = Form(...),
                    current_user: dict = Depends(auth.get_current_user_optional)):
    """Label a detected face with an employee ID"""

    # Get the video record
    video = upload_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Find the face in the video
    face_found = False
    if "faces" in video:
        for face in video["faces"]:
            if face["id"] == face_id:
                face["labeled"] = True
                face["employee_id"] = employee_id
                face["labeled_at"] = datetime.now().isoformat()
                face["labeled_by"] = current_user["id"] if current_user else None
                face_found = True
                break

    if not face_found:
        raise HTTPException(status_code=404, detail=f"Face {face_id} not found in video {video_id}")

    # Update the video record
    upload_manager.update_video_status(video_id, video["processing_status"], {
        "faces": video["faces"]
    })

    # Return success
    return {"status": "success", "message": f"Face {face_id} labeled with employee ID {employee_id}"}

# Face group API endpoints
@app.get("/api/face-groups")
async def get_face_groups(
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Get all face groups"""
    groups = face_group_manager.get_all_groups()
    return {"groups": groups}

@app.get("/api/face-groups/{group_id}")
async def get_face_group(
    group_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Get details for a specific face group"""
    group = face_group_manager.get_group(group_id)

    if not group:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

    return group

@app.post("/api/face-groups/{group_id}/label")
async def label_face_group(
    group_id: str,
    employee_id: str = Form(...),
    label: str = Form(...),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Label all faces in a group with an employee ID"""
    # Get the group
    group = face_group_manager.get_group(group_id)

    if not group:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

    # Label the group
    success = face_group_manager.label_group(group_id, employee_id, label)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to label group")

    # Now label all the individual faces in the group
    # This ensures the faces are labeled in their respective videos
    face_ids = group["face_ids"]
    labeled_faces = 0
    
    for face_id in face_ids:
        # Find which video this face belongs to
        for video in upload_manager.get_all_videos():
            if "faces" in video:
                face_found = False
                for face in video["faces"]:
                    if face["id"] == face_id:
                        # Label the face
                        face["labeled"] = True
                        face["employee_id"] = employee_id
                        face["label"] = label
                        face["labeled_at"] = datetime.now().isoformat()
                        face["labeled_by"] = current_user["id"] if current_user else None
                        face_found = True
                        labeled_faces += 1
                        break

                if face_found:
                    # Update the video record
                    upload_manager.update_video_status(video["id"], video["processing_status"], {
                        "faces": video["faces"]
                    })
                    break

    return {
        "status": "success",
        "message": f"Group {group_id} labeled with employee ID {employee_id}",
        "labeled_faces": labeled_faces
    }

# Cleanup API endpoints
@app.post("/api/cleanup/error-videos")
async def cleanup_error_videos(
    max_age_hours: Optional[int] = None,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """
    Clean up videos with error status or failed processing
    
    Args:
        max_age_hours: If provided, only clean up videos older than this many hours
        
    Returns:
        Cleanup operation results
    """
    # Only allow admin users to perform cleanup
    if not current_user or not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform cleanup operations"
        )
    
    try:
        # Run the cleanup operation
        result = cleanup_manager.cleanup_error_videos(max_age_hours)
        return result
    except Exception as e:
        logger.exception(f"Error during video cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}"
        )

@app.get("/api/cleanup/find-error-videos")
async def find_error_videos(
    max_age_hours: Optional[int] = None,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """
    Find videos with error status or failed processing without removing them
    
    Args:
        max_age_hours: If provided, only find videos older than this many hours
        
    Returns:
        List of error videos
    """
    try:
        # Find error videos
        error_videos = cleanup_manager.find_error_videos(max_age_hours)
        return {
            "error_videos": error_videos,
            "count": len(error_videos)
        }
    except Exception as e:
        logger.exception(f"Error finding error videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding error videos: {str(e)}"
        )

@app.get("/api/videos/{video_id}/face-groups")
async def get_video_face_groups(
    video_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Get all face groups in a video"""
    # Get the video
    video = upload_manager.get_video(video_id)

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Extract all group IDs from the faces in the video
    group_ids = set()
    if "faces" in video:
        for face in video["faces"]:
            if "group_id" in face and face["group_id"]:
                group_ids.add(face["group_id"])

    # Get the group details
    groups = [face_group_manager.get_group(group_id) for group_id in group_ids if face_group_manager.get_group(group_id)]

    return {"groups": groups}

# Parallel video processing endpoints
@app.post("/api/videos/{video_id}/parallel-process")
async def parallel_process_video(
    video_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """
    Process a video using the new parallel processing architecture.
    This separates upload validation, frame extraction, face detection,
    landmark processing, and grouping into independent stages.
    """
    # Get the video record
    video = upload_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Check if the video file exists
    if not os.path.exists(video["file_path"]):
        raise HTTPException(status_code=404, detail=f"Video file not found at {video['file_path']}")

    # Start the parallel processing
    job_id = parallel_face_processor.start_processing(video["file_path"])

    # Update the video record with the job ID
    upload_manager.update_video_status(video_id, "processing", {
        "parallel_job_id": job_id,
        "processing_started": datetime.now().isoformat()
    })

    return {
        "status": "processing",
        "job_id": job_id,
        "video_id": video_id,
        "message": "Video processing started in parallel"
    }

@app.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Get the status of a parallel processing job"""
    status = parallel_face_processor.get_processing_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return status

# Employees API endpoints
@app.get("/api/employees")
async def get_all_employees(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get all employees"""
    employees = employees_manager.get_all_employees()
    return employees

@app.get("/api/employees/search")
async def search_employees(q: str, current_user: dict = Depends(auth.get_current_user_optional)):
    """Search employees by name, department, position, etc."""
    employees = employees_manager.search_employees(q)
    return employees

@app.get("/api/employees/{employee_id}")
async def get_employee_by_id(employee_id: int, current_user: dict = Depends(auth.get_current_user_optional)):
    """Get a single employee by ID"""
    employee = employees_manager.get_employee_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return employee

@app.post("/api/employees")
async def create_employee(employee: Employee, current_user: dict = Depends(auth.get_current_user)):
    """Create a new employee"""
    # Convert Pydantic model to dict
    employee_data = employee.dict()
    
    new_employee = employees_manager.create_employee(employee_data)
    if not new_employee:
        raise HTTPException(status_code=500, detail="Failed to create employee")
    return new_employee

@app.put("/api/employees/{employee_id}")
async def update_employee(employee_id: int, employee: Employee, current_user: dict = Depends(auth.get_current_user)):
    """Update an existing employee"""
    # Convert Pydantic model to dict
    employee_data = employee.dict(exclude_unset=True)
    
    updated_employee = employees_manager.update_employee(employee_id, employee_data)
    if not updated_employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return updated_employee

@app.delete("/api/employees/{employee_id}")
async def delete_employee(employee_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete an employee"""
    success = employees_manager.delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return {"message": f"Employee {employee_id} deleted successfully"}

# Attendance API endpoints
@app.get("/api/attendance")
async def get_all_attendance(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get all attendance records"""
    records = attendance_manager.get_all_attendance()
    return records

@app.get("/api/attendance/date/{date}")
async def get_attendance_by_date(date: str, current_user: dict = Depends(auth.get_current_user_optional)):
    """Get attendance records for a specific date"""
    records = attendance_manager.get_attendance_by_date(date)
    return records

@app.post("/api/attendance")
async def create_attendance(attendance_data: Dict[str, Any] = Body(...), current_user: dict = Depends(auth.get_current_user_optional)):
    """Create a new attendance record"""
    record = attendance_manager.create_attendance(attendance_data)
    if not record:
        raise HTTPException(status_code=500, detail="Failed to create attendance record")
    return record

@app.put("/api/attendance/{attendance_id}")
async def update_attendance(attendance_id: int, attendance_data: Dict[str, Any] = Body(...), current_user: dict = Depends(auth.get_current_user_optional)):
    """Update an existing attendance record"""
    record = attendance_manager.update_attendance(attendance_id, attendance_data)
    if not record:
        raise HTTPException(status_code=404, detail=f"Attendance record {attendance_id} not found")
    return record

@app.delete("/api/attendance/{attendance_id}")
async def delete_attendance(attendance_id: int, current_user: dict = Depends(auth.get_current_user_optional)):
    """Delete an attendance record"""
    success = attendance_manager.delete_attendance(attendance_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Attendance record {attendance_id} not found")
    return {"message": f"Attendance record {attendance_id} deleted successfully"}

# Leave request API endpoints
@app.get("/api/leave-requests")
async def get_all_leave_requests(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get all leave requests"""
    requests = leave_manager.get_all_leave_requests()
    return requests

@app.get("/api/leave-requests/employee/{employee_id}")
async def get_employee_leave_requests(employee_id: int, current_user: dict = Depends(auth.get_current_user_optional)):
    """Get leave requests for a specific employee"""
    requests = leave_manager.get_employee_leave_requests(employee_id)
    return requests

@app.post("/api/leave-requests")
async def create_leave_request(request_data: Dict[str, Any] = Body(...), current_user: dict = Depends(auth.get_current_user_optional)):
    """Create a new leave request"""
    request = leave_manager.create_leave_request(request_data)
    if not request:
        raise HTTPException(status_code=500, detail="Failed to create leave request")
    return request

@app.put("/api/leave-requests/{request_id}")
async def update_leave_request(request_id: int, request_data: Dict[str, Any] = Body(...), current_user: dict = Depends(auth.get_current_user_optional)):
    """Update an existing leave request"""
    request = leave_manager.update_leave_request(request_id, request_data)
    if not request:
        raise HTTPException(status_code=404, detail=f"Leave request {request_id} not found")
    return request

@app.post("/api/leave-requests/{request_id}/approve")
async def approve_leave_request(request_id: int, request_data: Dict[str, Any] = Body(...), current_user: dict = Depends(auth.get_current_user)):
    """Approve a leave request"""
    approver_id = request_data.get("approverId", str(current_user.get("id", 0)))
    request = leave_manager.approve_leave_request(request_id, approver_id)
    if not request:
        raise HTTPException(status_code=404, detail=f"Leave request {request_id} not found")
    return request

@app.post("/api/leave-requests/{request_id}/reject")
async def reject_leave_request(request_id: int, request_data: Dict[str, Any] = Body(...), current_user: dict = Depends(auth.get_current_user)):
    """Reject a leave request"""
    reason = request_data.get("reason")
    request = leave_manager.reject_leave_request(request_id, reason)
    if not request:
        raise HTTPException(status_code=404, detail=f"Leave request {request_id} not found")
    return request

@app.delete("/api/leave-requests/{request_id}")
async def delete_leave_request(request_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a leave request"""
    success = leave_manager.delete_leave_request(request_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Leave request {request_id} not found")
    return {"message": f"Leave request {request_id} deleted successfully"}

# Dashboard API endpoints
@app.get("/api/dashboard/summary")
async def get_dashboard_summary(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get summary metrics for the dashboard"""
    summary = dashboard_manager.get_summary_metrics()
    return summary

@app.get("/api/attendance/today")
async def get_today_attendance(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get today's attendance records"""
    attendance = dashboard_manager.get_today_attendance()
    return attendance

@app.get("/api/leaves/upcoming")
async def get_upcoming_leaves(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get upcoming approved leave requests"""
    leaves = dashboard_manager.get_upcoming_leaves()
    return leaves

@app.get("/api/leaves/upcoming-absences")
async def get_upcoming_absences_data(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get data for upcoming absences for the next 7 days"""
    absences_data = dashboard_manager.get_upcoming_absences_data()
    return absences_data

# Scheduled cleanup task
async def run_scheduled_cleanup():
    """Run cleanup operations at regular intervals"""
    while True:
        try:
            # Wait 4 hours between cleanups
            await asyncio.sleep(4 * 60 * 60)  
            
            logger.info("Running scheduled cleanup tasks")
            
            # Clean up old jobs from memory
            background_processor.cleanup_old_jobs(24)  # Remove jobs older than 24 hours
            
            # Clean up error videos older than 7 days
            result = cleanup_manager.cleanup_error_videos(24 * 7)
            logger.info(f"Cleaned up {result.get('removed_count', 0)} error videos")
            
        except Exception as e:
            logger.exception(f"Error in scheduled cleanup: {str(e)}")
            # Sleep for a shorter period if there was an error
            await asyncio.sleep(30 * 60)  # 30 minutes

@app.on_event("startup")
async def startup_event():
    # Start the background processor
    background_processor.start()
    print("Started background processor")
    
    # Start the parallel background processor workers
    parallel_face_processor.background_processor.start_workers()
    print("Started parallel background processor workers")
    
    # Start the scheduled cleanup task
    asyncio.create_task(run_scheduled_cleanup())
    print("Started scheduled cleanup task")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown")
    # Stop the background processor
    background_processor.stop()

    # Stop the parallel background processor workers
    parallel_face_processor.background_processor.stop_workers()
    print("Stopped parallel background processor workers")

# User settings endpoints
@app.get("/api/users/me/settings", response_model=UserSettingsModel)
async def get_current_user_settings(current_user: dict = Depends(auth.get_current_user)):
    """Get the current user's settings"""
    db = next(get_db())
    settings_manager = UserSettingsManager(db)
    
    settings = settings_manager.get_user_settings(current_user["id"])
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return settings

@app.put("/api/users/me/settings", response_model=UserSettingsModel)
async def update_current_user_settings(settings: UserSettingsModel, current_user: dict = Depends(auth.get_current_user)):
    """Update the current user's settings"""
    db = next(get_db())
    settings_manager = UserSettingsManager(db)
    
    updated_settings = settings_manager.update_user_settings(
        user_id=current_user["id"],
        settings_data=settings.dict()
    )
    
    if not updated_settings:
        raise HTTPException(status_code=404, detail="Failed to update settings")
    
    return updated_settings

@app.put("/api/users/me/profile", response_model=UserResponse)
async def update_current_user_profile(profile: UserUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update the current user's profile"""
    # Use the existing update_user endpoint
    return await update_user(current_user["id"], profile, current_user)

@app.put("/api/users/me/password")
async def update_current_user_password(password_data: UserPasswordUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update the current user's password"""
    # Use the existing update_user_password endpoint
    return await update_user_password(current_user["id"], password_data, current_user)

# Role management endpoints
@app.get("/api/roles", response_model=List[RoleResponse])
async def get_all_roles(current_user: dict = Depends(auth.get_current_user_optional)):
    """Get all roles"""
    db = next(get_db())
    role_manager = RoleManager(db)
    
    roles = role_manager.get_all_roles()
    return roles

@app.get("/api/roles/with-user-counts", response_model=List[RoleWithUserCount])
async def get_roles_with_user_counts(current_user: dict = Depends(auth.get_current_user)):
    """Get all roles with user counts (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    role_manager = RoleManager(db)
    
    roles = role_manager.get_roles_with_user_counts()
    return roles

@app.get("/api/roles/search", response_model=List[RoleResponse])
async def search_roles(q: str, current_user: dict = Depends(auth.get_current_user_optional)):
    """Search roles by name or description"""
    db = next(get_db())
    role_manager = RoleManager(db)
    
    roles = role_manager.search_roles(q)
    return roles

@app.get("/api/roles/{role_id}", response_model=RoleResponse)
async def get_role_by_id(role_id: int, current_user: dict = Depends(auth.get_current_user_optional)):
    """Get a role by ID"""
    db = next(get_db())
    role_manager = RoleManager(db)
    
    role = role_manager.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role

@app.post("/api/roles", response_model=RoleResponse)
async def create_role(role: RoleCreate, current_user: dict = Depends(auth.get_current_user)):
    """Create a new role (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    role_manager = RoleManager(db)
    
    # Check if role name already exists
    existing_role = role_manager.get_role_by_name(role.name)
    if existing_role:
        raise HTTPException(status_code=400, detail="Role name already exists")
    
    new_role = role_manager.create_role(name=role.name, description=role.description)
    return new_role

@app.put("/api/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role: RoleUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update a role (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    role_manager = RoleManager(db)
    
    # Check if new role name already exists (if name is being changed)
    if role.name is not None:
        existing_role = role_manager.get_role_by_name(role.name)
        if existing_role and existing_role.id != role_id:
            raise HTTPException(status_code=400, detail="Role name already exists")
    
    updated_role = role_manager.update_role(role_id, name=role.name, description=role.description)
    if not updated_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return updated_role

@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Delete a role (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    role_manager = RoleManager(db)
    
    success = role_manager.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {"message": "Role deleted successfully"}

@app.get("/api/roles/{role_id}/users")
async def get_users_with_role(role_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Get all users with a specific role (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    role_manager = RoleManager(db)
    
    # Check if role exists
    role = role_manager.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    users = role_manager.get_users_with_role(role_id)
    return users

@app.post("/api/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(user_id: int, role_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Assign a role to a user (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    # Check if user and role exist
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # The role existence check is handled by the UserManager
    success = user_manager.assign_role_to_user(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {"message": f"Role assigned to user successfully"}

@app.delete("/api/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(user_id: int, role_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Remove a role from a user (requires admin privileges)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    # Check if user exists
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # The role existence check is handled by the UserManager
    success = user_manager.remove_role_from_user(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found or not assigned to user")
    
    return {"message": "Role removed from user successfully"}

@app.get("/api/users/{user_id}/roles")
async def get_user_roles(user_id: int, current_user: dict = Depends(auth.get_current_user)):
    """Get all roles for a user (requires admin privileges or be the same user)"""
    if not current_user.get("is_admin", False) and str(current_user.get("id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = next(get_db())
    user_manager = UserManager(db)
    
    # Check if user exists
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    roles = user_manager.get_user_roles(user_id)
    return roles

# Identity group API endpoints
@app.get("/api/identity-groups")
async def get_identity_groups(
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Get all identity groups"""
    groups = identity_group_manager.get_all_identities()
    return {"groups": groups}

@app.get("/api/face-sessions")
async def get_face_sessions(
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Alias for get_identity_groups to maintain compatibility with older clients"""
    groups = identity_group_manager.get_all_identities()
    return {"groups": groups}


@app.get("/api/face-files")
async def get_face_files():
    """Return a list of all available face image files"""
    face_files = []
    
    faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "faces")
    
    if os.path.exists(faces_dir):
        for file in os.listdir(faces_dir):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                # Extract the face ID from the filename
                face_id = os.path.splitext(file)[0]
                file_path = os.path.join(faces_dir, file)
                
                # Get file size and modification time
                stat = os.stat(file_path)
                
                face_files.append({
                    'id': face_id,
                    'filename': file,
                    'url': f"/static/faces/{file}",
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
    
    # Sort by modification time (newest first)
    face_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return {
        'count': len(face_files),
        'faces': face_files
    }
@app.get("/api/identity-groups/{identity_id}")
async def get_identity_group(
    identity_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Get details for a specific identity group"""
    group = identity_group_manager.get_identity(identity_id)

    if not group:
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")

    return group

@app.post("/api/identity-groups")
async def create_identity_group(
    data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Create a new identity group from a set of faces"""
    # Log the received data for debugging
    logger.info(f"Received identity group creation request with data: {data}")

    # Extract parameters from the request body
    face_ids = data.get("face_ids", [])
    name = data.get("name")
    primary_face_id = data.get("primary_face_id")
    video_ids = data.get("video_ids", [])

    logger.info(f"Processed parameters: face_ids={face_ids}, name={name}, primary_face_id={primary_face_id}, video_ids={video_ids}")

    if not face_ids:
        logger.error("Request missing face_ids or empty face_ids list")
        raise HTTPException(status_code=400, detail="At least one face ID is required")

    try:
        logger.info("About to call identity_group_manager.create_identity")
        identity_id = identity_group_manager.create_identity(
            face_ids=face_ids,
            name=name,
            primary_face_id=primary_face_id,
            video_ids=video_ids
        )
        logger.info(f"Successfully created identity group with ID: {identity_id}")
        
        # Ensure we always have a valid identity_id
        if not identity_id:
            logger.error("Failed to create identity group - no identity_id returned")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to create identity group - no identity ID generated"
            )

        # Also update the face records in their respective videos to have the identity_code
        for face_id in face_ids:
            for video in upload_manager.get_all_videos():
                if "faces" in video:
                    face_found = False
                    for face in video["faces"]:
                        if face["id"] == face_id:
                            # Update with identity code
                            face["identity_code"] = identity_id
                            face_found = True
                            break

                    if face_found:
                        # Update the video record
                        upload_manager.update_video_status(video["id"], video["processing_status"], {
                            "faces": video["faces"]
                        })

        logger.info("About to return successful response")
        response_data = {
            "status": "success",
            "identity_id": identity_id,
            "face_count": len(face_ids),
            "message": f"Created identity {identity_id} with {len(face_ids)} faces"
        }
        logger.info(f"Returning response: {response_data}")
        return response_data
    except Exception as e:
        logger.exception(f"Error creating identity group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating identity group: {str(e)}"
        )

@app.post("/api/identity-groups/{identity_id}/add-faces")
async def add_faces_to_identity(
    identity_id: str,
    data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Add faces to an existing identity group"""
    # Log the received data for debugging
    logger.info(f"Received request to add faces to identity {identity_id} with data: {data}")

    # Extract parameters from the request body
    face_ids = data.get("face_ids", [])
    video_ids = data.get("video_ids", [])

    logger.info(f"Processed parameters: face_ids={face_ids}, video_ids={video_ids}")

    if not face_ids:
        logger.error("Request missing face_ids or empty face_ids list")
        raise HTTPException(status_code=400, detail="At least one face ID is required")

    # Verify identity exists
    identity = identity_group_manager.get_identity(identity_id)
    if not identity:
        logger.error(f"Identity {identity_id} not found")
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")

    # Add faces to identity
    success = identity_group_manager.add_faces_to_identity(identity_id, face_ids, video_ids)
    if not success:
        logger.error(f"Failed to add faces to identity {identity_id}")
        raise HTTPException(status_code=500, detail=f"Failed to add faces to identity {identity_id}")

    logger.info(f"Successfully added {len(face_ids)} faces to identity {identity_id}")

    # Update the face records in their respective videos
    for face_id in face_ids:
        for video in upload_manager.get_all_videos():
            if "faces" in video:
                face_found = False
                for face in video["faces"]:
                    if face["id"] == face_id:
                        # Update with identity code
                        face["identity_code"] = identity_id
                        face_found = True
                        break

                if face_found:
                    # Update the video record
                    upload_manager.update_video_status(video["id"], video["processing_status"], {
                        "faces": video["faces"]
                    })

    return {
        "status": "success",
        "identity_id": identity_id,
        "added_faces": len(face_ids),
        "total_faces": len(identity["face_ids"]) + len(face_ids),
        "message": f"Added {len(face_ids)} faces to identity {identity_id}"
    }

@app.post("/api/identity-groups/{identity_id}/set-primary")
async def set_primary_face(
    identity_id: str,
    data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Set the primary (best quality) face for an identity"""
    # Log the received data for debugging
    logger.info(f"Received request to set primary face for identity {identity_id} with data: {data}")

    # Extract parameters from the request body
    face_id = data.get("face_id")

    if not face_id:
        logger.error("Request missing face_id parameter")
        raise HTTPException(status_code=400, detail="face_id is required")

    # Verify identity exists
    identity = identity_group_manager.get_identity(identity_id)
    if not identity:
        logger.error(f"Identity {identity_id} not found")
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")

    # Verify face is in this identity
    if face_id not in identity["face_ids"]:
        logger.error(f"Face {face_id} is not part of identity {identity_id}")
        raise HTTPException(status_code=400, detail=f"Face {face_id} is not part of identity {identity_id}")

    # Set primary face
    success = identity_group_manager.set_primary_face(identity_id, face_id)
    if not success:
        logger.error(f"Failed to set primary face for identity {identity_id}")
        raise HTTPException(status_code=500, detail=f"Failed to set primary face for identity {identity_id}")

    logger.info(f"Successfully set primary face {face_id} for identity {identity_id}")

    return {
        "status": "success",
        "identity_id": identity_id,
        "primary_face_id": face_id,
        "message": f"Set primary face for identity {identity_id}"
    }

@app.post("/api/identity-groups/{identity_id}/assign-employee")
async def assign_employee_to_identity(
    identity_id: str,
    data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Assign an employee ID to an identity group"""
    # Log the received data for debugging
    logger.info(f"Received request to assign employee to identity {identity_id} with data: {data}")

    # Extract parameters from the request body
    employee_id = data.get("employee_id")

    if not employee_id:
        logger.error("Request missing employee_id parameter")
        raise HTTPException(status_code=400, detail="employee_id is required")

    # Verify identity exists
    identity = identity_group_manager.get_identity(identity_id)
    if not identity:
        logger.error(f"Identity {identity_id} not found")
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")

    # Assign employee to identity
    success = identity_group_manager.assign_employee(identity_id, employee_id)
    if not success:
        logger.error(f"Failed to assign employee {employee_id} to identity {identity_id}")
        raise HTTPException(status_code=500, detail=f"Failed to assign employee to identity {identity_id}")

    logger.info(f"Successfully assigned employee {employee_id} to identity {identity_id}")

    # Now label all faces in the identity with this employee
    for face_id in identity["face_ids"]:
        for video in upload_manager.get_all_videos():
            if "faces" in video:
                face_found = False
                for face in video["faces"]:
                    if face["id"] == face_id:
                        face["labeled"] = True
                        face["employee_id"] = employee_id
                        face["labeled_at"] = datetime.now().isoformat()
                        face["labeled_by"] = current_user["id"] if current_user else None
                        face_found = True
                        break

                if face_found:
                    # Update the video record
                    upload_manager.update_video_status(video["id"], video["processing_status"], {
                        "faces": video["faces"]
                    })

    return {
        "status": "success",
        "identity_id": identity_id,
        "employee_id": employee_id,
        "message": f"Assigned employee {employee_id} to identity {identity_id}"
    }

@app.delete("/api/videos/{video_id}/faces/{face_id}")
async def delete_face(
    video_id: str,
    face_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """
    Delete a face from a video
    
    This endpoint:
    1. Removes the face from the video record
    2. Removes the face from any face groups
    3. Removes the face from any identity groups
    4. Optionally deletes the face image file
    """
    logger.info(f"Deleting face {face_id} from video {video_id}")
    
    # Get the video
    video = upload_manager.get_video(video_id)
    if not video:
        logger.error(f"Video not found: {video_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Video not found: {video_id}"
        )
    
    # Check if the video has a faces array
    if "faces" not in video or not video["faces"]:
        logger.error(f"Video {video_id} has no faces")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No faces found in video {video_id}"
        )
    
    # Find the face in the video
    face = None
    face_index = -1
    for i, f in enumerate(video["faces"]):
        if f["id"] == face_id:
            face = f
            face_index = i
            break
    
    if face is None:
        logger.error(f"Face {face_id} not found in video {video_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Face {face_id} not found in video {video_id}"
        )
    
    # 1. Remove the face from any face groups
    try:
        # Get the group ID for this face
        group_id = face_group_manager.groups["face_memberships"].get(face_id)
        if group_id:
            logger.info(f"Removing face {face_id} from face group {group_id}")
            face_group_manager.remove_face_from_group(group_id, face_id)
    except Exception as e:
        logger.error(f"Error removing face from face group: {str(e)}")
        # Continue with deletion even if this fails
    
    # 2. Remove the face from any identity groups
    try:
        # Get the identity ID for this face
        identity_id = identity_group_manager.identities["face_memberships"].get(face_id)
        if identity_id:
            logger.info(f"Removing face {face_id} from identity group {identity_id}")
            identity_group_manager.remove_face_from_identity(identity_id, face_id)
    except Exception as e:
        logger.error(f"Error removing face from identity group: {str(e)}")
        # Continue with deletion even if this fails
    
    # 3. Remove the face from the video record
    video["faces"].pop(face_index)
    upload_manager.update_video_status(video_id, video["processing_status"], {"faces": video["faces"]})
    
    # 4. Optionally delete the face image file
    if "imageUrl" in face and face["imageUrl"] and face["imageUrl"].startswith("/static/faces/"):
        # Extract filename from image URL
        try:
            face_filename = os.path.basename(face["imageUrl"])
            face_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "faces", face_filename)
            
            if os.path.exists(face_path):
                logger.info(f"Deleting face image file: {face_path}")
                os.remove(face_path)
        except Exception as e:
            logger.error(f"Error deleting face image file: {str(e)}")
            # Don't fail the request if file deletion fails
    
    logger.info(f"Successfully deleted face {face_id} from video {video_id}")
    return {"status": "success", "message": f"Face {face_id} deleted from video {video_id}"}

@app.delete("/api/identity-groups/{identity_id}/faces/{face_id}")
async def remove_face_from_identity_group(
    identity_id: str,
    face_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Remove a face from an identity group but keep the face"""
    # Verify identity exists
    identity = identity_group_manager.get_identity(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")
    
    # Check if face is in the identity
    if face_id not in identity["face_ids"]:
        raise HTTPException(status_code=404, detail=f"Face {face_id} not found in identity {identity_id}")
    
    # Get video containing the face to update it later
    face_video_id = None
    for video in upload_manager.get_all_videos():
        if "faces" in video:
            for face in video["faces"]:
                if face["id"] == face_id:
                    face_video_id = video["id"]
                    # Remove identity_code from the face
                    if "identity_code" in face:
                        del face["identity_code"]
                    break
            if face_video_id:
                # Update the video record
                upload_manager.update_video_status(video["id"], video["processing_status"], {
                    "faces": video["faces"]
                })
                break
    
    # Remove face from identity group
    success = identity_group_manager.remove_face_from_identity(identity_id, face_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to remove face from identity {identity_id}")
    
    return {
        "status": "success", 
        "message": f"Removed face {face_id} from identity {identity_id}"
    }

# Custom endpoint for removing a face from any identity group
@app.post("/api/custom/remove-face-from-group")
async def custom_remove_face_from_group(
    face_id: str = Body(..., embed=True),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Custom endpoint to remove a face from any identity group it belongs to"""
    logger.info(f"Custom remove face from group API called for face_id: {face_id}")
    
    # First, find which identity group the face belongs to
    face_identity = None
    
    # Look in groups
    for identity_id, identity in identity_group_manager.identities.get("groups", {}).items():
        if "face_ids" in identity and face_id in identity["face_ids"]:
            face_identity = identity_id
            break
    
    if not face_identity:
        # If we can't find the identity, check face_memberships
        face_identity = identity_group_manager.identities.get("face_memberships", {}).get(face_id)
        
    logger.info(f"Found face in identity group: {face_identity}")
    
    if not face_identity:
        return {
            "status": "success",
            "message": f"Face {face_id} is not associated with any identity group"
        }
    
    # Now update all videos that contain this face
    updated_videos = []
    for video in upload_manager.get_all_videos():
        if "faces" in video:
            updated = False
            for face in video["faces"]:
                if face["id"] == face_id:
                    # Remove identity_code from the face
                    if "identity_code" in face:
                        del face["identity_code"]
                        updated = True
                    
                    # Ensure labeled is set to false
                    face["labeled"] = False
                    updated = True
            
            if updated:
                # Update the video record with explicit save
                upload_manager.update_video_status(video["id"], video["processing_status"], {
                    "faces": video["faces"]
                })
                # Force save
                upload_manager._save_uploads()
                updated_videos.append(video["id"])
    
    logger.info(f"Updated faces in videos: {updated_videos}")
    
    # Double-check that the identity group exists
    identity = identity_group_manager.get_identity(face_identity)
    if not identity:
        logger.warning(f"Identity {face_identity} not found despite being referenced")
        return {
            "status": "partial_success",
            "message": f"Removed face {face_id} from videos but couldn't find identity group {face_identity}"
        }
    
    # Remove from the identity group
    logger.info(f"Removing face {face_id} from identity group {face_identity}")
    
    # Check if face is in the group's face_ids list
    if face_id in identity["face_ids"]:
        logger.info(f"Face {face_id} found in identity {face_identity} face_ids list, removing...")
        success = identity_group_manager.remove_face_from_identity(face_identity, face_id)
        logger.info(f"Removed face from identity result: {success}")
    else:
        logger.warning(f"Face {face_id} not found in identity {face_identity} face_ids list")
        # Remove it from face_memberships directly
        if face_id in identity_group_manager.identities["face_memberships"]:
            del identity_group_manager.identities["face_memberships"][face_id]
            identity_group_manager._save_identities()
            logger.info(f"Removed face {face_id} from face_memberships")
            success = True
        else:
            logger.warning(f"Face {face_id} not found in face_memberships")
            success = False
    
    return {
        "status": "success", 
        "message": f"Removed face {face_id} from identity {face_identity}",
        "identity_id": face_identity,
        "updated_videos": updated_videos
    }

@app.delete("/api/identity-groups/{identity_id}")
async def delete_identity_group(
    identity_id: str,
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Delete an identity group"""
    # Verify identity exists
    identity = identity_group_manager.get_identity(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")

    # For each face in the identity, remove the identity_code from its video record
    for face_id in identity["face_ids"]:
        for video in upload_manager.get_all_videos():
            if "faces" in video:
                face_found = False
                for face in video["faces"]:
                    if face["id"] == face_id and "identity_code" in face:
                        # Remove the identity code
                        del face["identity_code"]
                        face_found = True
                        break

                if face_found:
                    # Update the video record
                    upload_manager.update_video_status(video["id"], video["processing_status"], {
                        "faces": video["faces"]
                    })

    # Delete the identity
    success = identity_group_manager.delete_identity(identity_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete identity {identity_id}")

    return {
        "status": "success",
        "message": f"Deleted identity {identity_id}"
    }

@app.post("/api/identity-groups/merge")
async def merge_identity_groups(
    data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(auth.get_current_user_optional)
):
    """Merge multiple identity groups into a target identity"""
    # Log the received data for debugging
    logger.info(f"Received request to merge identity groups with data: {data}")

    # Extract parameters from the request body
    source_ids = data.get("source_ids", [])
    target_id = data.get("target_id")

    if not source_ids:
        logger.error("Request missing source_ids or empty source_ids list")
        raise HTTPException(status_code=400, detail="At least one source identity ID is required")

    if not target_id:
        logger.error("Request missing target_id parameter")
        raise HTTPException(status_code=400, detail="target_id is required")

    # Verify target identity exists
    target = identity_group_manager.get_identity(target_id)
    if not target:
        logger.error(f"Target identity {target_id} not found")
        raise HTTPException(status_code=404, detail=f"Target identity {target_id} not found")

    # Merge identities
    success = identity_group_manager.merge_identities(source_ids, target_id)
    if not success:
        logger.error(f"Failed to merge identities {source_ids} into {target_id}")
        raise HTTPException(status_code=500, detail=f"Failed to merge identities into {target_id}")

    logger.info(f"Successfully merged identities {source_ids} into {target_id}")

    # Update identity_code for all faces from source identities to target identity
    for video in upload_manager.get_all_videos():
        if "faces" in video:
            update_needed = False
            for face in video["faces"]:
                if "identity_code" in face and face["identity_code"] in source_ids:
                    face["identity_code"] = target_id
                    update_needed = True

            if update_needed:
                # Update the video record
                upload_manager.update_video_status(video["id"], video["processing_status"], {
                    "faces": video["faces"]
                })

    return {
        "status": "success",
        "target_id": target_id,
        "merged_identities": len(source_ids),
        "total_faces": len(target["face_ids"]),
        "message": f"Merged {len(source_ids)} identities into {target_id}"
    }

# Mount the Gradio app AFTER all API routes are defined
app.mount("/", gr.routes.App(demo))

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting server at http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)