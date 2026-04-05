@echo off
echo =========================================
echo Setting up Gesture VFX Application
echo =========================================
echo.
echo Installing required Python packages...
pip install opencv-python mediapipe pygame moderngl numpy

echo.
echo Starting Application...
python main.py

pause
