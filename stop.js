module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: [
          // Kill any processes using port 9002 (Next.js)
          "echo 'Stopping any processes using port 9002...'",
          "kill -9 $(lsof -t -i:9002 2>/dev/null) 2>/dev/null || echo 'No process using port 9002'",
          
          // Kill any processes using port 3000 (default Next.js port)
          "echo 'Stopping any processes using port 3000...'",
          "kill -9 $(lsof -t -i:3000 2>/dev/null) 2>/dev/null || echo 'No process using port 3000'",
          
          // Kill any processes using port 7860 (Python backend)
          "echo 'Stopping any processes using port 7860...'",
          "kill -9 $(lsof -t -i:7860 2>/dev/null) 2>/dev/null || echo 'No process using port 7860'",
          
          // Alternative approach using ss if lsof is not available
          "echo 'Attempting alternative port cleanup...'",
          "for pid in $(ss -tulpn | grep ':9002\\|:3000\\|:7860' | awk '{print $7}' | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u); do kill -9 $pid 2>/dev/null || echo \"Could not kill PID $pid\"; done",
          
          "echo 'All processes stopped.'"
        ],
        on: [{
          "event": "All processes stopped.",
          "done": true
        }]
      }
    }
  ]
}