"""
Petra Library Seat Detection - Real-time Stream Server
Menggunakan Flask + SocketIO untuk streaming detection results ke web frontend
"""

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
import threading
import time
import cv2
import mss
import numpy as np
import json
import os
from pathlib import Path

# Import detection modules
from src.detector import SeatDetector
from src.utils import load_seat_zones
from src.config import SEAT_ZONES_PATH

# ==================== FLASK APP SETUP ====================
app = Flask(__name__, 
            static_folder='Web/frontend',
            template_folder='Web/frontend')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ==================== GLOBAL STATE ====================
detector = None
seat_zones = None
is_running = False
monitor_roi = None
detection_thread = None

# Status mapping untuk frontend
STATUS_MAP = {
    'OCCUPIED': 1,  # Red
    'ON-HOLD': 2,   # Yellow
    'EMPTY': 3      # Green
}

# ==================== ROUTES ====================
@app.route('/')
def index():
    """Serve main HTML page"""
    return render_template('index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory('Web/frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory('Web/frontend/js', filename)

@app.route('/data/<path:filename>')
def serve_data(filename):
    """Serve data files"""
    return send_from_directory('Web/frontend/data', filename)

# ==================== DETECTION LOGIC ====================
def load_monitor_roi():
    """Load saved ROI coordinates from setup"""
    roi_path = 'config/monitor_roi.json'
    
    if not os.path.exists(roi_path):
        print("❌ ERROR: monitor_roi.json not found!")
        print("   Please run setup_roi.py first to select monitoring area")
        return None
    
    with open(roi_path, 'r') as f:
        roi = json.load(f)
    
    print(f"✅ Loaded ROI: {roi['width']}x{roi['height']} at ({roi['left']}, {roi['top']})")
    return roi

def detection_loop():
    """
    Main detection loop yang jalan di background thread
    Capture frame -> Detect -> Send via WebSocket
    """
    global is_running, detector, seat_zones, monitor_roi
    
    sct = mss.mss()
    frame_count = 0
    
    print("\n" + "="*60)
    print("  🔴 DETECTION LOOP STARTED")
    print("="*60)
    
    while is_running:
        try:
            start_time = time.time()
            
            # 1. Capture frame dari screen area yang dipilih
            img = np.array(sct.grab(monitor_roi))
            frame = img[:, :, :3]  # BGRA -> BGR
            
            # 2. Run YOLO detection + mapping ke seat zones
            all_detections, seat_statuses = detector.process_image(frame, seat_zones)
            
            # 3. Convert hasil deteksi ke format yang frontend expect
            status_codes = {}
            for seat_id, data in seat_statuses.items():
                status_code = STATUS_MAP.get(data['status'], 3)
                status_codes[seat_id.upper()] = status_code
            
            # 4. Prepare data packet
            output_data = {
                "timestamp": time.strftime("%H:%M:%S"),
                "status_codes": status_codes
            }
            
            # 5. Kirim via WebSocket ke semua connected clients
            socketio.emit('status_update', output_data)
            
            # Performance metrics
            elapsed = time.time() - start_time
            frame_count += 1
            
            if frame_count % 10 == 0:  # Print every 10 frames
                fps = 1.0 / elapsed if elapsed > 0 else 0
                print(f"[Frame {frame_count}] FPS: {fps:.1f} | "
                      f"Detections: {len(all_detections)} | "
                      f"Occupied: {list(status_codes.values()).count(1)}")
            
            # Control update rate (1 FPS = 1 second interval)
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"❌ Error in detection loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)
    
    print("\n⏹️  Detection loop stopped")

# ==================== SOCKETIO EVENTS ====================
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'✅ Client connected: {request.sid}')
    
    # Send initial status
    socketio.emit('connection_status', {
        'status': 'connected',
        'message': 'Connected to detection server'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'❌ Client disconnected: {request.sid}')

@socketio.on('start_detection')
def start_detection():
    """
    Start detection when requested from frontend
    Loads model, seat zones, and starts detection thread
    """
    global is_running, detector, seat_zones, monitor_roi, detection_thread
    
    if is_running:
        socketio.emit('error', {'message': 'Detection already running'})
        return
    
    try:
        print("\n" + "="*60)
        print("  🚀 STARTING DETECTION SYSTEM")
        print("="*60)
        
        # 1. Load monitor ROI
        print("\n[1/4] Loading monitor ROI...")
        monitor_roi = load_monitor_roi()
        if monitor_roi is None:
            socketio.emit('error', {
                'message': 'Monitor ROI not configured. Please run setup_roi.py first.'
            })
            return
        
        # 2. Load seat zones
        print("[2/4] Loading seat zones...")
        seat_zones = load_seat_zones(SEAT_ZONES_PATH)
        print(f"      ✓ Loaded {len(seat_zones)} seat zones: {list(seat_zones.keys())}")
        
        # 3. Initialize YOLO detector
        print("[3/4] Initializing YOLO detector...")
        detector = SeatDetector()
        print("      ✓ Detector ready")
        
        # 4. Start detection thread
        print("[4/4] Starting detection thread...")
        is_running = True
        detection_thread = threading.Thread(target=detection_loop, daemon=True)
        detection_thread.start()
        print("      ✓ Detection thread started")
        
        print("\n✅ Detection system started successfully!")
        print("="*60 + "\n")
        
        # Notify frontend
        socketio.emit('detection_started', {
            'message': 'Detection started successfully',
            'seats': list(seat_zones.keys())
        })
        
    except Exception as e:
        print(f"❌ Failed to start detection: {e}")
        import traceback
        traceback.print_exc()
        
        socketio.emit('error', {
            'message': f'Failed to start detection: {str(e)}'
        })

@socketio.on('stop_detection')
def stop_detection():
    """Stop detection when requested from frontend"""
    global is_running
    
    if not is_running:
        socketio.emit('error', {'message': 'Detection not running'})
        return
    
    print("\n⏹️  Stopping detection...")
    is_running = False
    
    socketio.emit('detection_stopped', {
        'message': 'Detection stopped'
    })
    
    print("✅ Detection stopped\n")

# ==================== MAIN ====================
if __name__ == '__main__':
    from flask import request
    
    print("\n" + "="*60)
    print("  PETRA LIBRARY SEAT DETECTION - STREAM SERVER")
    print("="*60)
    print("\n📍 Server Configuration:")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: 5000")
    print(f"   URL:  http://localhost:5000")
    print("\n📋 Prerequisites:")
    print("   1. Run setup_roi.py first to configure monitoring area")
    print("   2. Ensure seat_zones.json is configured correctly")
    print("   3. Make sure YOLOv8 model is downloaded")
    print("\n" + "="*60)
    print("\n🚀 Starting server...\n")
    
    # Create config directory if not exists
    Path('config').mkdir(exist_ok=True)
    
    # Run server
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=5000, 
                 debug=False,  # Set False untuk production
                 allow_unsafe_werkzeug=True)