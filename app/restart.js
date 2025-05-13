const { exec } = require('child_process');
const path = require('path');

console.log("Stopping existing processes...");

// Kill any existing Python and Node.js processes for this application
exec("pkill -f 'python app.py' && pkill -f 'next dev'", (error, stdout, stderr) => {
  if (error) {
    console.log("Warning: Could not kill all processes, they may not be running.");
  } else {
    console.log("Existing processes stopped.");
  }
  
  console.log("Waiting 3 seconds before restarting...");
  
  // Wait 3 seconds before restarting
  setTimeout(() => {
    console.log("Restarting application...");
    
    // Start the main script using node
    const startScript = path.join(__dirname, '..', 'start.js');
    const pinokioProcess = exec(`cd .. && node -e "require('./pinokio').run(require('./start'))"`, {
      cwd: path.join(__dirname, '..'),
    });
    
    pinokioProcess.stdout.on('data', (data) => {
      console.log(`stdout: ${data}`);
    });
    
    pinokioProcess.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
    });
    
    pinokioProcess.on('close', (code) => {
      console.log(`Child process exited with code ${code}`);
    });
    
    console.log("Restart initiated. Check application logs for progress.");
  }, 3000);
});