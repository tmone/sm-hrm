# StepmediaHRM - Pinokio App

A Pinokio application that integrates a Next.js frontend with a Python backend for HR management with facial recognition capabilities.

## Overview

StepmediaHRM provides a complete HR management solution with:

- Modern Next.js frontend
- Python backend with facial recognition using Gradio
- Seamless integration between both components

## Installation

1. Install this template in Pinokio
2. Click "Install" from the Pinokio interface
3. Wait for the installation to complete
4. Click "Start" to run the application
5. Access the application through the "Open Web UI" button

## Architecture

This application uses:

- Next.js for the frontend UI
- Python backend with FastAPI and Gradio
- Integration through REST API calls

## Development

The application structure is:

- Python backend (`app.py`) - Provides facial recognition API and Gradio UI
- Next.js frontend (`app/src`) - Provides the web interface for the HR system
- Pinokio scripts handle running both components together

See the README.md in the `app` directory for more detailed development instructions.

## Troubleshooting

If you encounter any issues:

1. Check that both the Next.js frontend and Python backend are running
2. Ensure the Python backend URL is correctly set in the environment variables
3. Check for any errors in the terminal logs
4. Restart the application if necessary

