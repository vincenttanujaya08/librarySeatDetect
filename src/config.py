# Configuration file for Library Seat Detection System

# YOLO Model Configuration
YOLO_MODEL = "yolov8s.pt"  # Options: yolov8n.pt, yolov8s.pt, yolov8m.pt
CONFIDENCE_THRESHOLD = 0.25  # Minimum confidence for detection
IOU_THRESHOLD = 0.1  # Minimum IoU for object-seat mapping

# COCO Class IDs (from YOLO pretrained on COCO dataset)
CLASS_PERSON = 0
CLASS_BACKPACK = 24
CLASS_LAPTOP = 63
CLASS_BOOK = 73
CLASS_CELL_PHONE = 67
CLASS_BOTTLE = 39
CLASS_CUP = 41

# Classes to detect
DETECT_CLASSES = [
    CLASS_PERSON,
    CLASS_BACKPACK,
    CLASS_LAPTOP,
    CLASS_BOOK
]

# Object weights for occupancy scoring (higher = more important)
OBJECT_WEIGHTS = {
    CLASS_PERSON: 10.0,      # Highest priority
    CLASS_BACKPACK: 5.0,
    CLASS_LAPTOP: 4.0,
    CLASS_BOOK: 2.0,
    CLASS_CELL_PHONE: 1.0,
    CLASS_BOTTLE: 0.5,
    CLASS_CUP: 0.5
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

# Seat status definitions
STATUS_OCCUPIED = "OCCUPIED"
STATUS_ON_HOLD = "ON-HOLD"
STATUS_EMPTY = "EMPTY"

# Visualization colors (BGR format for OpenCV)
COLOR_OCCUPIED = (0, 255, 0)      # Green
COLOR_ON_HOLD = (0, 165, 255)     # Orange
COLOR_EMPTY = (0, 0, 255)         # Red
COLOR_SEAT_ZONE = (0, 255, 255)   # Yellow

# Detection colors by class
DETECTION_COLORS = {
    CLASS_PERSON: (0, 255, 0),      # Green
    CLASS_BACKPACK: (255, 0, 0),    # Blue
    CLASS_LAPTOP: (0, 165, 255),    # Orange
    CLASS_BOOK: (255, 0, 255),      # Magenta
}

# Paths
SEAT_ZONES_PATH = "data/seat_zones.json"
OUTPUT_DIR = "outputs"
ANNOTATED_DIR = "outputs/annotated_images"