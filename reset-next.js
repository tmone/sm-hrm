module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: [
          "cd /home/tmone/pinokio/api/StepmediaHRM/app",
          "pkill -f 'next dev' || true",
          "rm -rf .next",
          "npm run dev"
        ]
      }
    }
  ]
}