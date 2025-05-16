import os
import json
import uuid
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ExternalYOLOTrainer:
    """
    YOLO trainer that uses external scripts to avoid server restarts
    """
    
    def __init__(self):
        """Initialize the external YOLO trainer"""
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self.training_dir = os.path.join(self.base_dir, "training")
        self.datasets_dir = os.path.join(self.training_dir, "datasets")
        self.models_dir = os.path.join(self.training_dir, "models")
        
        # Create directories
        os.makedirs(self.datasets_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        
        # In-memory job tracking
        self.jobs = {}
        
    def start_training(self, group_ids: List[str], epochs: int = 10, batch_size: int = 4) -> str:
        """Start training job using external scripts"""
        job_id = str(uuid.uuid4())
        
        # Create job record
        self.jobs[job_id] = {
            'id': job_id,
            'status': 'queued',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'group_ids': group_ids,
            'message': 'Training job queued',
            'error': None,
            'epochs': epochs,
            'batch_size': batch_size
        }
        
        # Start training in background thread
        thread = threading.Thread(
            target=self._run_training, 
            args=(job_id, group_ids, epochs, batch_size)
        )
        thread.daemon = True
        thread.start()
        
        return job_id
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training job"""
        job = self.jobs.get(job_id)
        
        if job:
            # Check for status file from external script
            status_file = os.path.join(self.training_dir, f"{job_id}_status.json")
            if os.path.exists(status_file):
                try:
                    with open(status_file, 'r') as f:
                        external_status = json.load(f)
                        job.update(external_status)
                except Exception as e:
                    logger.error(f"Error reading status file: {e}")
        
        return job
        
    def _run_training(self, job_id: str, group_ids: List[str], epochs: int, batch_size: int):
        """Run the training using external scripts"""
        try:
            # Update job status
            self.jobs[job_id]['status'] = 'processing'
            self.jobs[job_id]['progress'] = 10
            self.jobs[job_id]['message'] = 'Preparing dataset'
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
            # Step 1: Prepare YOLO dataset
            prepare_script = os.path.join(self.training_dir, "prepare_yolo_dataset.py")

            # Use the virtual environment's Python
            venv_python = os.path.join(self.base_dir, "env", "bin", "python")
            if not os.path.exists(venv_python):
                venv_python = "python3"  # Fallback to system python

            prepare_cmd = [
                venv_python, prepare_script,
                "--job-id", job_id,
                "--groups", json.dumps(group_ids),
                "--output-dir", self.datasets_dir
            ]

            logger.info(f"Running dataset preparation: {' '.join(prepare_cmd)}")

            # Change to app directory for proper import paths
            original_dir = os.getcwd()
            os.chdir(self.base_dir)

            try:
                # Set environment for subprocess
                env = os.environ.copy()
                env['PYTHONPATH'] = self.base_dir

                prepare_result = subprocess.run(prepare_cmd, capture_output=True, text=True, env=env)

                if prepare_result.returncode != 0:
                    logger.error(f"Dataset preparation stderr: {prepare_result.stderr}")
                    logger.error(f"Dataset preparation stdout: {prepare_result.stdout}")
                    raise Exception(f"Dataset preparation failed: {prepare_result.stderr}")

                logger.info(f"Dataset preparation completed successfully")
                logger.info(f"Dataset preparation output: {prepare_result.stdout[:500]}...")  # Log first 500 chars

            finally:
                os.chdir(original_dir)
            
            # Wait for dataset preparation to complete and read metadata
            dataset_metadata_file = os.path.join(self.training_dir, f"{job_id}_dataset.json")

            # Wait for file to be created (max 30 seconds)
            for i in range(30):
                if os.path.exists(dataset_metadata_file):
                    break
                logger.info(f"Waiting for dataset metadata file... {i+1}/30")
                import time
                time.sleep(1)

            if not os.path.exists(dataset_metadata_file):
                raise Exception(f"Dataset metadata file not found: {dataset_metadata_file}")

            with open(dataset_metadata_file, 'r') as f:
                dataset_metadata = json.load(f)
            
            dataset_yaml = dataset_metadata['yaml_path']
            
            # Update status
            self.jobs[job_id]['progress'] = 30
            self.jobs[job_id]['message'] = 'Starting YOLO training'
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
            # Step 2: Train YOLO model
            train_script = os.path.join(self.training_dir, "train_yolo_model.py")
            train_cmd = [
                venv_python, train_script,
                "--job-id", job_id,
                "--dataset", dataset_yaml,
                "--epochs", str(epochs),
                "--batch", str(batch_size),
                "--imgsz", "320"  # Small image size for memory efficiency
            ]
            
            logger.info(f"Running YOLO training: {' '.join(train_cmd)}")
            
            # Run training in subprocess with proper environment
            process = subprocess.Popen(
                train_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,  # Use the same environment
                cwd=self.base_dir  # Set working directory
            )
            
            # Monitor training output
            for line in process.stdout:
                logger.info(f"YOLO training: {line.strip()}")
                
                # Update progress based on output
                if "Epoch" in line:
                    try:
                        # Extract epoch number from output
                        epoch_num = int(line.split()[1].split('/')[0])
                        progress = 30 + (60 * epoch_num // epochs)
                        self.jobs[job_id]['progress'] = progress
                        self.jobs[job_id]['message'] = f'Training epoch {epoch_num}/{epochs}'
                        self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
                    except:
                        pass
            
            process.wait()
            
            if process.returncode != 0:
                raise Exception("YOLO training failed")
            
            # Read training result
            result_file = os.path.join(self.training_dir, f"{job_id}_result.json")
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            # Update job status
            self.jobs[job_id]['status'] = 'completed'
            self.jobs[job_id]['progress'] = 100
            self.jobs[job_id]['message'] = f'Training completed successfully'
            self.jobs[job_id]['model_path'] = result['model_path']
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
            logger.info(f"Training job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Training job {job_id} failed: {str(e)}")
            self.jobs[job_id]['status'] = 'failed'
            self.jobs[job_id]['progress'] = 0
            self.jobs[job_id]['message'] = 'Training failed'
            self.jobs[job_id]['error'] = str(e)
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
    
    def test_model(self, model_path: str, video_path: str, progress_callback=None) -> Dict[str, Any]:
        """Test the trained model on a video using multi-threading"""
        try:
            logger.info(f"[DEBUG] test_model called with model_path={model_path}, video_path={video_path}")
            
            # Check if video_path is None
            if video_path is None:
                logger.error("[DEBUG] Video path is None!")
                return {'success': False, 'error': 'No video path provided'}
            
            # Verify files exist
            if not os.path.exists(model_path):
                logger.error(f"[DEBUG] Model file does not exist: {model_path}")
                return {'success': False, 'error': f'Model file not found: {model_path}'}
            
            if not os.path.exists(video_path):
                logger.error(f"[DEBUG] Video file does not exist: {video_path}")
                return {'success': False, 'error': f'Video file not found: {video_path}'}
            
            # Import the multi-threaded tester
            from db.multi_thread_tester import MultiThreadVideoTester

            logger.info(f"[DEBUG] Testing model: {model_path} on video: {video_path} using multi-threading")

            # Create multi-threaded tester
            tester = MultiThreadVideoTester(max_workers=4)

            # Test the video
            logger.info("[DEBUG] Calling tester.test_video")
            result = tester.test_video(
                model_path=model_path,
                video_path=video_path,
                progress_callback=progress_callback
            )
            
            logger.info(f"[DEBUG] Test result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error testing model: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

# Create singleton instance
external_yolo_trainer = ExternalYOLOTrainer()