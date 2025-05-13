const { exec } = require('child_process');
const path = require('path');

console.log("Stopping Python processes...");

// Kill any existing Python processes for this application
exec("pkill -f 'python app.py'", (error, stdout, stderr) => {
  if (error) {
    console.log("Warning: Could not kill Python processes, they may not be running.");
  } else {
    console.log("Python processes stopped.");
  }
  
  console.log("Waiting 2 seconds before restarting...");
  
  // Wait 2 seconds before restarting
  setTimeout(() => {
    console.log("Restarting Python backend...");
    
    // Start Python app in a new process
    const pythonProcess = exec(`cd ${__dirname} && python app.py`, {
      cwd: __dirname,
      env: {
        ...process.env,
        PORT: "7860"
      }
    });
    
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python error: ${data}`);
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
    });
    
    console.log("Python backend restart initiated.");
  }, 2000);
});