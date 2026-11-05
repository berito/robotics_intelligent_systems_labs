#!/usr/bin/env bash
# Create .venv (with access to the ROS 2 packages), install requirements.txt and download
# the YOLO models into robot_perception/models/. Safe to run again.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "Creating the virtual environment in .venv"
    python3 -m venv --system-site-packages .venv
fi
# keep colcon out of the venv
touch .venv/COLCON_IGNORE

.venv/bin/pip install --quiet --upgrade pip
# CPU build: about 200 MB, against over 3 GB for the CUDA build
echo "Installing PyTorch (CPU build)"
.venv/bin/pip install --progress-bar on torch torchvision --index-url https://download.pytorch.org/whl/cpu
echo "Installing the other Python packages"
.venv/bin/pip install --progress-bar on -r requirements.txt

echo "Downloading the YOLO models into robot_perception/models/"
.venv/bin/python - <<'PYTHON'
from ultralytics import YOLO

for path in ("robot_perception/models/yolov8n.pt", "robot_perception/models/yolov8n-seg.pt"):
    YOLO(path)
    print(f"  {path}")
PYTHON

.venv/bin/python -c "import cv_bridge, torch; print('cv_bridge works; PyTorch', torch.__version__)"
echo "Done. In every terminal: source $(pwd)/.venv/bin/activate"
