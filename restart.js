module.exports = {
  daemon: true,
  run: [
    // Kill existing processes by port to ensure all instances are stopped
    {
      method: "shell.run",
      params: {
        message: [
          "echo 'Stopping any existing processes...'",
          // Kill processes by name
          "pkill -f 'python app.py' || echo 'Python not running'",
          "pkill -f 'next dev' || echo 'Next.js not running'",

          // Kill any processes using port 9002 (Next.js)
          "kill -9 $(lsof -t -i:9002 2>/dev/null) 2>/dev/null || echo 'No process using port 9002'",
          // Kill any processes using port 3000 (default Next.js port)
          "kill -9 $(lsof -t -i:3000 2>/dev/null) 2>/dev/null || echo 'No process using port 3000'",
          // Kill any processes using port 7860 (Python backend)
          "kill -9 $(lsof -t -i:7860 2>/dev/null) 2>/dev/null || echo 'No process using port 7860'",

          // Alternative approach using ss if lsof is not available
          "for pid in $(ss -tulpn | grep ':9002\\|:3000\\|:7860' | awk '{print $7}' | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u 2>/dev/null); do kill -9 $pid 2>/dev/null || echo \"Could not kill PID $pid\"; done",

          "echo 'All processes stopped.'",
          "sleep 2" // Wait for ports to be freed
        ],
        on: [{
          "event": "All processes stopped.",
          "done": true
        }]
      }
    },
    // Install Python dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",                // Python virtual environment
        path: "app",                // Path to start the shell from
        message: [
          "pip install -r requirements.txt",  // Install Python dependencies
        ]
      }
    },
    // Start Python backend
    {
      method: "shell.run",
      params: {
        venv: "env",                // Python virtual environment
        env: {
          PORT: "7860"              // Port for Python backend
        },
        path: "app",                // Path to start the shell from
        message: [
          "python app.py",          // Start Python backend
        ],
        on: [{
          // When this pattern occurs in the shell terminal, proceed to next step
          "event": "/http:\/\/\\S+/",
          "done": true              // Keep shell alive and move to next step
        }]
      }
    },
    {
      // Set the Python backend URL
      method: "local.set",
      params: {
        python_url: "{{input.event[0]}}"
      }
    },
    // Start Next.js frontend
    {
      method: "shell.run",
      params: {
        path: "app",                // Path to start the shell from
        env: {
          // Set environment variable for Python backend URL
          "NEXT_PUBLIC_PYTHON_BACKEND_URL": "{{local.python_url}}",
          "JWT_SECRET": "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        },
        message: [
          "npm run dev"             // Start Next.js development server
        ],
        on: [{
          // When this pattern occurs, proceed to next step
          "event": "/ready|Ready/ - started server on/",
          "done": true              // Keep shell alive and move to next step
        }]
      }
    },
    {
      // Set the local variable 'url' for the Next.js frontend
      method: "local.set",
      params: {
        // Use the Next.js frontend URL
        url: "http://localhost:9002"
      }
    }
  ]
}