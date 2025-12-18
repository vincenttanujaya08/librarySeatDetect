"""
Petra Library Seat Detection - Main Server
Real-time detection with Flask + SocketIO + Preprocessing + Temporal Smoothing

Usage: python run_server.py
"""

from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO
from flask_cors import CORS
import threading
import time
import cv2
import mss
import numpy as np
import json
import os
import webbrowser
from pathlib import Path

# Import detection modules
from src.detector import SeatDetector
from src.preprocessor import ImagePreprocessor
from src.temporal_smoother import TemporalSmoother
from src.utils import load_seat_zones
from src.config import *

# ==================== APP SETUP ====================
app = Flask(__name__, 
            static_folder='web',
            template_folder='web')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ==================== GLOBAL STATE ====================
detector = None
preprocessor = None
smoother = None
seat_zones = None
is_running = False
detection_thread = None

# ==================== ROUTES ====================
@app.route('/')
def index():
    """Serve main HTML page"""
    return render_template('index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory('web/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory('web/js', filename)

# ==================== CONFIG CHECKING ====================
def check_config_exists():
    """Check if seat_zones.json exists"""
    zones_path = SEAT_ZONES_PATH
    
    if not os.path.exists(zones_path):
        print("\n" + "="*70)
        print("  ❌ ERROR: Configuration not found")
        print("="*70)
        print(f"\n{zones_path} not found!")
        print("\nPlease run setup first:")
        print("  $ python setup_zones.py")
        print()
        return False
    
    return True

# ==================== DETECTION LOOP ====================
def detection_loop():
    """
    Main detection loop running in background thread
    
    Pipeline:
    1. Capture frame from ROI
    2. Preprocess (optional): CLAHE, denoise, sharpen, etc
    3. YOLO Detection
    4. Map to seat zones
    5. Temporal Smoothing (anti-flickering)
    6. Send to frontend via WebSocket
    """
    global is_running, detector, preprocessor, smoother, seat_zones
    
    sct = mss.mss()
    frame_count = 0
    
    print("\n" + "="*70)
    print("  🔴 DETECTION STARTED")
    print("="*70)
    print("\nPress Ctrl+C to stop\n")
    
    while is_running:
        try:
            start_time = time.time()
            
            # ===== STEP 1: CAPTURE =====
            img = np.array(sct.grab(MONITOR_ROI))
            frame = img[:, :, :3]  # BGRA -> BGR
            
            # ===== STEP 2: PREPROCESSING (optional) =====
            if PREPROCESSING_ENABLED:
                frame = preprocessor.process(frame)
            
            # ===== STEP 3: YOLO DETECTION + SEAT MAPPING =====
            all_detections, seat_statuses = detector.process_frame(frame, seat_zones)
            
            # ===== STEP 4: TEMPORAL SMOOTHING (anti-flickering) =====
            if TEMPORAL_SMOOTHING_ENABLED:
                # Extract raw statuses
                raw_statuses = {seat_id: data['status'] 
                               for seat_id, data in seat_statuses.items()}
                
                # Apply temporal smoothing
                smoothed_statuses_dict = smoother.update_batch(raw_statuses)
                
                # Rebuild seat_statuses with smoothed status
                smoothed_seat_statuses = {}
                for seat_id, data in seat_statuses.items():
                    smoothed_seat_statuses[seat_id] = {
                        'status': smoothed_statuses_dict[seat_id],
                        'detected_objects': data['detected_objects'],
                        'reason': data['reason']
                    }
                
                seat_statuses = smoothed_seat_statuses
            
            # ===== STEP 5: CONVERT TO FRONTEND FORMAT =====
            status_codes = {}
            for seat_id, data in seat_statuses.items():
                status_code = STATUS_MAP.get(data['status'], 3)
                status_codes[seat_id.upper()] = status_code
            
            # ===== STEP 6: PREPARE DATA PACKET =====
            output_data = {
                "timestamp": time.strftime("%H:%M:%S"),
                "status_codes": status_codes
            }
            
            # ===== STEP 7: SEND VIA WEBSOCKET =====
            socketio.emit('status_update', output_data)
            
            # ===== PERFORMANCE METRICS =====
            elapsed = time.time() - start_time
            frame_count += 1
            
            if frame_count % 10 == 0:
                fps = 1.0 / elapsed if elapsed > 0 else 0
                occupied_count = list(status_codes.values()).count(1)
                
                # Build status string
                status_str = f"[Frame {frame_count}] FPS: {fps:.1f} | "
                status_str += f"Detections: {len(all_detections)} | "
                status_str += f"Occupied: {occupied_count}/6"
                
                # Add smoothing info if enabled
                if TEMPORAL_SMOOTHING_ENABLED:
                    status_str += f" | Smoothing: {TEMPORAL_METHOD}"
                
                print(status_str)
            
            # Control update rate
            sleep_time = max(0, (1.0 / UPDATE_RATE_FPS) - elapsed)
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"❌ Error in detection: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)
    
    print("\n⏹️  Detection stopped")

# ==================== SOCKETIO EVENTS ====================
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'✅ Client connected')
    socketio.emit('connection_status', {
        'status': 'connected',
        'message': 'Connected to detection server'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'❌ Client disconnected')

@socketio.on('start_detection')
def start_detection():
    """Start detection loop"""
    global is_running, detector, preprocessor, smoother, seat_zones, detection_thread
    
    if is_running:
        # Silently ignore if already running (not an error)
        print("ℹ️  Detection already running, skipping duplicate start request")
        socketio.emit('detection_started', {
            'message': 'Detection already running',
            'seats': list(seat_zones.keys()) if seat_zones else []
        })
        return
    
    try:
        print("\n" + "="*70)
        print("  🚀 INITIALIZING DETECTION SYSTEM")
        print("="*70)
        
        # 1. Load seat zones
        print("\n[1/4] Loading seat zones...")
        seat_zones = load_seat_zones(SEAT_ZONES_PATH)
        print(f"      ✓ {len(seat_zones)} seats: {list(seat_zones.keys())}")
        
        # 2. Initialize YOLO detector
        print("[2/4] Initializing YOLO detector...")
        detector = SeatDetector()
        print("      ✓ Detector ready")
        
        # 3. Initialize preprocessor
        print("[3/4] Initializing preprocessor...")
        preprocessor = ImagePreprocessor()
        if PREPROCESSING_ENABLED:
            features = []
            if PREPROCESSING_CLAHE:
                features.append("CLAHE")
            if PREPROCESSING_HIST_EQ:
                features.append("HistEq")
            if PREPROCESSING_DENOISE:
                features.append("Denoise")
            if PREPROCESSING_SHARPEN:
                features.append("Sharpen")
            print(f"      ✓ Preprocessing ENABLED: {', '.join(features) if features else 'Basic adjustments'}")
        else:
            print("      ✓ Preprocessing DISABLED")
        
        # 4. Initialize temporal smoother
        print("[4/4] Initializing temporal smoother...")
        if TEMPORAL_SMOOTHING_ENABLED:
            smoother = TemporalSmoother(
                window_size=TEMPORAL_WINDOW_SIZE,
                method=TEMPORAL_METHOD
            )
            print(f"      ✓ Temporal smoothing ENABLED: {TEMPORAL_METHOD} (window={TEMPORAL_WINDOW_SIZE})")
        else:
            smoother = None
            print("      ✓ Temporal smoothing DISABLED")
        
        # Start detection thread
        is_running = True
        detection_thread = threading.Thread(target=detection_loop, daemon=True)
        detection_thread.start()
        
        print("\n✅ All systems initialized successfully!")
        print("="*70 + "\n")
        
        # Notify frontend
        socketio.emit('detection_started', {
            'message': 'Detection started successfully',
            'seats': list(seat_zones.keys())
        })
        
    except Exception as e:
        print(f"\n❌ Failed to start: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error', {
            'message': f'Failed to start detection: {str(e)}'
        })

@socketio.on('stop_detection')
def stop_detection():
    """Stop detection loop"""
    global is_running
    
    if not is_running:
        socketio.emit('error', {'message': 'Detection not running'})
        return
    
    print("\n⏹️  Stopping detection...")
    is_running = False
    
    socketio.emit('detection_stopped', {
        'message': 'Detection stopped'
    })

# ==================== MAIN ====================
def open_browser_delayed(url, delay=2):
    """Open browser after delay"""
    time.sleep(delay)
    print(f"\n🌐 Opening browser: {url}\n")
    webbrowser.open(url)

def print_header():
    """Print server header with config info"""
    print("\n" + "="*70)
    print("  PETRA LIBRARY SEAT DETECTION - SERVER")
    print("="*70)
    print(f"\n📡 Server: http://localhost:{SERVER_PORT}")
    print(f"📂 Config: {SEAT_ZONES_PATH}")
    print(f"📦 Model: {YOLO_MODEL}")
    print(f"🔄 Update Rate: {UPDATE_RATE_FPS} FPS")
    print()
    print("⚙️  Features:")
    print(f"   Preprocessing: {'✅ ENABLED' if PREPROCESSING_ENABLED else '❌ DISABLED'}")
    if PREPROCESSING_ENABLED:
        if PREPROCESSING_CLAHE:
            print(f"      - CLAHE (clip={CLAHE_CLIP_LIMIT}, grid={CLAHE_GRID_SIZE})")
        if PREPROCESSING_HIST_EQ:
            print(f"      - Histogram Equalization")
        if PREPROCESSING_DENOISE:
            print(f"      - Denoising (strength={DENOISE_STRENGTH})")
        if PREPROCESSING_SHARPEN:
            print(f"      - Sharpening (strength={SHARPEN_STRENGTH})")
    
    print(f"   Temporal Smoothing: {'✅ ENABLED' if TEMPORAL_SMOOTHING_ENABLED else '❌ DISABLED'}")
    if TEMPORAL_SMOOTHING_ENABLED:
        print(f"      - Method: {TEMPORAL_METHOD}")
        print(f"      - Window: {TEMPORAL_WINDOW_SIZE} frames")
        if TEMPORAL_METHOD == 'hysteresis':
            print(f"      - Threshold: {HYSTERESIS_THRESHOLD} consecutive frames")
    
    print("\n" + "="*70 + "\n")

def main():
    """Main entry point"""
    print_header()
    
    # Check config exists
    if not check_config_exists():
        return
    
    # Schedule browser opening
    print("⏳ Starting server...")
    print("   Browser will open automatically in 2 seconds...")
    
    browser_thread = threading.Thread(
        target=open_browser_delayed, 
        args=(f'http://localhost:{SERVER_PORT}', 2),
        daemon=True
    )
    browser_thread.start()
    
    # Run server
    try:
        socketio.run(app, 
                     host=SERVER_HOST, 
                     port=SERVER_PORT, 
                     debug=False,
                     allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
        print("✅ Shutdown complete\n")

if __name__ == "__main__":
    main()