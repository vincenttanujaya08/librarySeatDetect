# ==================== CONFIGURATION ====================
# Library Seat Detection System - Configuration File

# ==================== HARDCODED ROI ====================
# Koordinat ROI untuk Photo Booth / Camera (FIXED - tidak perlu setup)
# Format: {left, top, width, height} dalam pixel
MONITOR_ROI = {
    "left": 1204,
    "top": 380,
    "width": 595,
    "height": 393
}

# ==================== MODEL CONFIGURATION ====================
YOLO_MODEL = "models/yolov8s.pt"
CONFIDENCE_THRESHOLD = 0.25  # Global threshold
IOU_THRESHOLD = 0.1          # Minimum IoU for object-seat mapping

# ==================== DETECTION CLASSES ====================
# COCO Class IDs
CLASS_PERSON = 0
CLASS_BACKPACK = 24
CLASS_LAPTOP = 63
CLASS_BOOK = 73
CLASS_CELL_PHONE = 67
CLASS_BOTTLE = 39
CLASS_CUP = 41

# Classes to detect (prioritas deteksi)
DETECT_CLASSES = [
    CLASS_PERSON,
    CLASS_BACKPACK,
    CLASS_LAPTOP,
    CLASS_BOOK
]

# Class-specific confidence thresholds
# Adjust ini kalau false positive terlalu banyak atau miss detection
CLASS_THRESHOLDS = {
    CLASS_PERSON: 0.3,      # Higher untuk person (reduce false positive)
    CLASS_BACKPACK: 0.25,
    CLASS_LAPTOP: 0.25,
    CLASS_BOOK: 0.1,        # Lower untuk book (susah detect di meja)
    CLASS_CELL_PHONE: 0.25,
    CLASS_BOTTLE: 0.30,
    CLASS_CUP: 0.30
}

# Class names mapping
CLASS_NAMES = {
    CLASS_PERSON: "person",
    CLASS_BACKPACK: "backpack",
    CLASS_LAPTOP: "laptop",
    CLASS_BOOK: "book",
    CLASS_CELL_PHONE: "cell phone",
    CLASS_BOTTLE: "bottle",
    CLASS_CUP: "cup"
}

# ==================== SEAT STATUS ====================
STATUS_OCCUPIED = "OCCUPIED"  # Ada orang
STATUS_ON_HOLD = "ON-HOLD"    # Ada barang tapi ga ada orang
STATUS_EMPTY = "EMPTY"         # Kosong

# Status codes untuk frontend (1=Occupied, 2=On-Hold, 3=Empty)
STATUS_MAP = {
    STATUS_OCCUPIED: 1,
    STATUS_ON_HOLD: 2,
    STATUS_EMPTY: 3
}

# Visualization colors (BGR format untuk OpenCV)
COLOR_OCCUPIED = (0, 0, 255)      # Red
COLOR_ON_HOLD = (0, 165, 255)     # Orange
COLOR_EMPTY = (0, 255, 0)         # Green
COLOR_SEAT_ZONE = (0, 255, 255)   # Yellow

# Detection colors by class
DETECTION_COLORS = {
    CLASS_PERSON: (0, 255, 0),      # Green
    CLASS_BACKPACK: (255, 0, 0),    # Blue
    CLASS_LAPTOP: (0, 165, 255),    # Orange
    CLASS_BOOK: (255, 0, 255),      # Magenta
}

# ==================== PREPROCESSING ====================
# Enable/disable preprocessing sebelum masuk YOLO
PREPROCESSING_ENABLED = True  # Set True untuk enable

# Basic adjustments
PREPROCESSING_BRIGHTNESS = 1.0  # 1.0 = normal, >1.0 = brighter, <1.0 = darker
PREPROCESSING_CONTRAST = 1.0    # 1.0 = normal, >1.0 = more contrast

# Histogram Equalization (pilih salah satu: HIST_EQ atau CLAHE)
PREPROCESSING_HIST_EQ = True  # Simple histogram equalization
PREPROCESSING_CLAHE = False     # Adaptive histogram eq (RECOMMENDED untuk varying light)

# CLAHE settings (hanya jika CLAHE enabled)
CLAHE_CLIP_LIMIT = 2.0          # 1.0-4.0, higher = more contrast
CLAHE_GRID_SIZE = (8, 8)        # Grid size for local equalization

# Denoising (bisa bikin lambat)
PREPROCESSING_DENOISE = False   # Enable/disable denoising
DENOISE_STRENGTH = 10           # Denoising strength (3-30)

# Sharpening
PREPROCESSING_SHARPEN = False   # Enable/disable sharpening
SHARPEN_STRENGTH = 1.0          # Sharpening strength (0.5-2.0)

# ==================== TEMPORAL SMOOTHING ====================
# Anti-flickering: Smooth status changes over time
TEMPORAL_SMOOTHING_ENABLED = True  # RECOMMENDED: Enable untuk reduce flickering

# Window settings
TEMPORAL_WINDOW_SIZE = 3        # Number of frames to consider (3-10)
                                # Larger = more stable, tapi slower response

# Smoothing method
TEMPORAL_METHOD = 'majority_voting'  # Options:
                                      # - 'majority_voting': Most common status in window (RECOMMENDED)
                                      # - 'hysteresis': Require N consecutive frames to change
                                      # - 'exponential': Weighted average (recent = higher weight)

# Hysteresis settings (hanya jika method = 'hysteresis')
HYSTERESIS_THRESHOLD = 3        # Consecutive frames needed to change status (2-5)

# Exponential smoothing settings (hanya jika method = 'exponential')
EXPONENTIAL_ALPHA = 0.3         # Smoothing factor (0-1), lower = smoother

# ==================== PATHS ====================
SEAT_ZONES_PATH = "config/seat_zones.json"
OUTPUT_DIR = "outputs"

# ==================== SERVER CONFIGURATION ====================
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5050
UPDATE_RATE_FPS = 1  # Berapa kali per detik update (1 = 1 FPS)

# ==================== USAGE NOTES ====================
# 
# PREPROCESSING COMBINATIONS:
# - Low light: Enable CLAHE (clip_limit=2.0-3.0)
# - Noisy image: Enable DENOISE (strength=10-20) - WARNING: SLOW
# - Blurry image: Enable SHARPEN (strength=1.0-1.5)
# - Varying light: Enable CLAHE instead of HIST_EQ
#
# TEMPORAL SMOOTHING:
# - Flickering banyak: Increase WINDOW_SIZE (5→7)
# - Response terlalu lambat: Decrease WINDOW_SIZE (5→3)
# - Rapid oscillation: Use 'hysteresis' method
# - Smooth animation: Use 'exponential' method
#