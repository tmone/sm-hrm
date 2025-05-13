#!/bin/bash
echo "Installing required dependencies for face landmarks and grouping"

# Install dlib system dependencies (required for building dlib)
apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libboost-all-dev

# Activate the virtual environment
source env/bin/activate

# Install dependencies within the virtual environment
pip install --upgrade pip
pip install dlib
pip install scikit-learn
pip install bz2file

# Ensure bcrypt is installed at the correct version for passlib compatibility
pip install bcrypt==3.2.2

echo "Dependencies installed successfully!"