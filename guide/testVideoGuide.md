# Library Seat Occupation Detector - Video & Webcam Guide

## Overview
This guide covers how to use the video and real-time detection features of your library seat occupation detection system.

## Project Structure
```
project/
├── detect_image.py          # Single image detection (existing)
├── detect_video.py          # Video file detection (NEW)
├── detect_webcam.py         # Real-time webcam/IP camera detection (NEW)
├── test_yolo_raw.py         # Raw YOLO testing (existing)
├── src/
│   ├── detector.py          # SeatDetector class
│   ├── utils.py             # Utility functions
│   └── config.py            # Configuration
├── data/
│   ├── test_images/         # Test images
│   ├── test_videos/         # Test videos (create this)
│   └── seat_zones.json      # Seat zone definitions
└── output/
    ├── annotated/           # Annotated outputs
    └── snapshots/           # Webcam snapshots
```

---

## 1. Video File Detection (`detect_video.py`)

### Basic Usage

**Process a video file:**
```bash
python detect_video.py --video data/test_videos/library_video.mp4
```

### Advanced Options

**Skip frames for faster processing:**
```bash
python detect_video.py --video data/test_videos/library_video.mp4 --skip-frames 3
```
This processes every 3rd frame, making it 3x faster.

**Run without display (background processing):**
```bash
python detect_video.py --video data/test_videos/library_video.mp4 --no-display
```

**Process without saving output video:**
```bash
python detect_video.py --video data/test_videos/library_video.mp4 --no-save
```

**Custom seat zones:**
```bash
python detect_video.py --video data/test_videos/library_video.mp4 --zones custom_zones.json
```

### Controls During Playback
- **`q`** - Quit processing
- **`p`** - Pause/Resume

### Output
- Annotated video saved to: `output/annotated/[video_name]_annotated.mp4`
- Progress updates printed every 30 frames
- Final statistics at the end

---

## 2. Real-time Detection (`detect_webcam.py`)

### Using Default Webcam

**Start detection with your computer's webcam:**
```bash
python detect_webcam.py
```

### Using IP Webcam App (Phone Camera)

#### Step 1: Setup IP Webcam on Phone
1. Install **"IP Webcam"** app on your Android phone (or similar app for iOS)
2. Open the app and scroll down
3. Tap **"Start server"**
4. Note the URL shown at the bottom (e.g., `http://192.168.1.100:8080`)

#### Step 2: Connect from Computer
Make sure your computer and phone are on the **same WiFi network**, then:

```bash
# Replace with your phone's IP address
python detect_webcam.py --source http://192.168.100.107:8080/video
```

**Common IP Webcam URLs:**
- Video stream: `http://[PHONE_IP]:8080/video`
- Photo (single frame): `http://[PHONE_IP]:8080/photo.jpg`
- High quality video: `http://[PHONE_IP]:8080/video?1920x1080`

### Advanced Options

**Skip frames for better performance:**
```bash
python detect_webcam.py --source 0 --skip-frames 3
```

**Disable snapshot saving:**
```bash
python detect_webcam.py --source 0 --no-snapshots
```

**Use different webcam (if you have multiple):**
```bash
python detect_webcam.py --source 1
```

### Controls During Live Detection
- **`q`** - Quit
- **`s`** - Save snapshot (image + JSON report)
- **`p`** - Pause/Resume
- **`r`** - Reset FPS counter

### Output
- Live display with overlay information
- Snapshots saved to: `output/snapshots/snapshot_[timestamp].jpg`
- JSON reports saved with each snapshot

---

## 3. Testing Workflow

### Phase 1: Test with Video File
1. Record a short video of your library (10-30 seconds)
2. Place it in `data/test_videos/`
3. Run: `python detect_video.py --video data/test_videos/video1.mp4`
4. Verify that detection works correctly

### Phase 2: Test with Webcam
1. Position your webcam to view test area
2. Run: `python detect_webcam.py`
3. Adjust seat zones if needed based on camera angle
4. Test all controls (save snapshot, pause, etc.)

### Phase 3: Deploy with IP Webcam
1. Setup IP Webcam on phone
2. Mount phone in fixed position in library
3. Connect: `python detect_webcam.py --source http://[PHONE_IP]:8080/video`
4. Monitor performance and save snapshots periodically

---

## 4. Performance Optimization

### If Processing is Slow

**1. Increase frame skipping:**
```bash
--skip-frames 5  # Process every 5th frame
```

**2. Reduce video resolution (for IP Webcam):**
- In IP Webcam app settings, reduce video resolution to 720p or 640x480

**3. Use a lighter YOLO model:**
In your `src/detector.py`, change:
```python
model = YOLO('yolov8n.pt')  # Nano model (fastest)
# instead of yolov8s.pt (small model)
```

**4. Adjust detection confidence:**
Lower confidence threshold processes faster but may reduce accuracy.

### Recommended Settings by Use Case

| Use Case | skip-frames | Model | Resolution |
|----------|-------------|-------|------------|
| High accuracy analysis | 1 | yolov8s | 1080p |
| Real-time monitoring | 2-3 | yolov8n | 720p |
| Resource-constrained | 5 | yolov8n | 480p |

---

## 5. Troubleshooting

### Video Detection Issues

**Problem: "Could not open video"**
- Check file path is correct
- Ensure video format is supported (MP4, AVI, MOV)
- Try converting video: `ffmpeg -i input.mov -c:v libx264 output.mp4`

**Problem: Video plays too fast/slow**
- Check FPS of source video: `ffprobe video.mp4`
- Adjust `--skip-frames` parameter

### Webcam/IP Camera Issues

**Problem: "Could not connect to camera"**
- **Default webcam:** Check if another application is using it
- **IP Webcam:** 
  - Verify phone and computer are on same network
  - Check firewall isn't blocking port 8080
  - Try pinging phone IP: `ping 192.168.1.100`
  - Test URL in browser first: `http://192.168.1.100:8080`

**Problem: High latency/lag**
- Reduce resolution in IP Webcam settings
- Increase `--skip-frames` value
- Ensure strong WiFi signal
- Use 5GHz WiFi if available

**Problem: Detection is inaccurate**
- Ensure seat zones are correctly defined for camera angle
- Adjust detection confidence in `src/detector.py`
- Check lighting conditions (YOLO works better with good lighting)
- Recalibrate seat zones for current camera position

---

## 6. Creating Test Data

### Recording Test Videos

**With Phone:**
1. Record video in landscape mode
2. Keep phone steady (use tripod if available)
3. Ensure good lighting
4. Record for 10-30 seconds
5. Transfer to `data/test_videos/`

**With Webcam (using OpenCV):**
```python
import cv2

cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test_video.mp4', fourcc, 20.0, (640, 480))

print("Recording... Press 'q' to stop")
while True:
    ret, frame = cap.read()
    if ret:
        out.write(frame)
        cv2.imshow('Recording', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
```

---

## 7. Next Steps

### Integration Ideas
1. **Database logging:** Store seat status to database every minute
2. **Web dashboard:** Create Flask/FastAPI server to display live status
3. **Alert system:** Send notifications when occupancy reaches threshold
4. **Analytics:** Track occupancy patterns over time
5. **Multiple cameras:** Monitor different library areas simultaneously

### Example: Simple Web Server
```python
# In detect_webcam.py, add Flask endpoint
from flask import Flask, Response
import json

app = Flask(__name__)
current_status = {}

@app.route('/status')
def get_status():
    return json.dumps(current_status)

# Update current_status in main loop
# Run Flask in separate thread
```

---

## 8. Command Reference

### detect_video.py
```bash
python detect_video.py --video VIDEO_PATH [OPTIONS]

Options:
  --video PATH          Input video file (required)
  --zones PATH          Seat zones JSON file (default: data/seat_zones.json)
  --output PATH         Output directory (default: output/)
  --skip-frames N       Process every Nth frame (default: 1)
  --no-display          Don't show video during processing
  --no-save            Don't save annotated video
```

### detect_webcam.py
```bash
python detect_webcam.py [OPTIONS]

Options:
  --source SOURCE       Camera source: 0 for webcam, URL for IP camera (default: 0)
  --zones PATH          Seat zones JSON file (default: data/seat_zones.json)
  --skip-frames N       Process every Nth frame (default: 2)
  --no-snapshots        Disable snapshot saving
```

---

## Need Help?

If you encounter issues:
1. Check that `src/detector.py`, `src/utils.py`, and `src/config.py` are working
2. Test with a single image first: `python detect_image.py --image test.jpg`
3. Verify your seat zones JSON is correctly formatted
4. Check that YOLO model file (`yolov8s.pt`) is downloaded
5. Ensure all dependencies are installed: `pip install ultralytics opencv-python`

Good luck with your library seat detection system! 🎯📚