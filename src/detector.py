"""
Seat Detector
YOLO-based object detection + seat mapping logic
"""

from ultralytics import YOLO
import cv2
import numpy as np
from src.config import *
from src.utils import is_object_in_seat


class SeatDetector:
    """
    YOLO detector untuk deteksi objek dan mapping ke seat zones
    """
    
    def __init__(self, model_path=YOLO_MODEL):
        """
        Initialize YOLO model
        
        Args:
            model_path: Path to YOLO model (.pt file)
        """
        print(f"📦 Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        print("✅ Model loaded successfully")
    
    def detect_objects(self, image):
        """
        Run YOLO detection dengan class-specific thresholds
        
        Args:
            image: Input image (BGR)
        
        Returns:
            list: List of detections [{'class_id', 'class_name', 'confidence', 'bbox'}]
        """
        # Run YOLO dengan threshold rendah dulu (catch all)
        results = self.model.predict(
            image,
            classes=DETECT_CLASSES,
            conf=0.10,  # Low threshold untuk catch all dulu
            verbose=False
        )
        
        detections = []
        
        # Parse results dan apply class-specific thresholds
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                
                # Apply class-specific threshold
                min_conf = CLASS_THRESHOLDS.get(class_id, 0.25)
                
                if confidence < min_conf:
                    continue  # Skip low confidence detections
                
                detection = {
                    'class_id': class_id,
                    'class_name': CLASS_NAMES.get(class_id, 'unknown'),
                    'confidence': confidence,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)]
                }
                
                detections.append(detection)
        
        return detections
    
    def filter_background_objects(self, detections, seat_zones):
        """
        Filter objek yang jauh dari seat zones (background objects)
        
        Args:
            detections: List of detections
            seat_zones: Dict of seat zones
        
        Returns:
            list: Filtered detections
        """
        if not seat_zones:
            return detections
        
        # Calculate area covering all seats
        all_x1 = min(zone[0] for zone in seat_zones.values())
        all_y1 = min(zone[1] for zone in seat_zones.values())
        all_x2 = max(zone[2] for zone in seat_zones.values())
        all_y2 = max(zone[3] for zone in seat_zones.values())
        
        # Expand dengan margin (untuk catch objek di pinggir seat)
        margin = 100
        valid_area = [
            all_x1 - margin,
            all_y1 - margin,
            all_x2 + margin,
            all_y2 + margin
        ]
        
        filtered = []
        for det in detections:
            # Check if object center in valid area
            obj_center_x = (det['bbox'][0] + det['bbox'][2]) / 2
            obj_center_y = (det['bbox'][1] + det['bbox'][3]) / 2
            
            if (valid_area[0] <= obj_center_x <= valid_area[2] and
                valid_area[1] <= obj_center_y <= valid_area[3]):
                filtered.append(det)
        
        return filtered
    
    def map_detections_to_seats(self, detections, seat_zones):
        """
        Map detected objects ke seat zones dengan priority-based assignment
        
        Priority:
        1. Seat dengan person → assign semua objek yang overlap
        2. Seat tanpa person → assign sisa objek yang overlap
        
        Args:
            detections: List of detections
            seat_zones: Dict of seat zones
        
        Returns:
            dict: {seat_id: {'status': str, 'detected_objects': [...], 'reason': str}}
        """

         # -------------------------------
        # Helper functions
        # -------------------------------
        def bbox_center(b):
            return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

        def distance(p1, p2):
            return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
        
        # Separate persons dan objects
        person_detections = []
        object_detections = []
        
        for det in detections:
            if det['class_id'] == CLASS_PERSON:
                person_detections.append(det)
            else:
                object_detections.append(det)
        
        # -------------------------------
        # Precompute seat centers
        # -------------------------------
        seat_centers = {
            seat_id: bbox_center(seat_bbox)
            for seat_id, seat_bbox in seat_zones.items()
        }

        # -------------------------------
        # Phase 1 — Assign each person to ONE closest seat
        # -------------------------------
        seats_with_person = {seat_id: [] for seat_id in seat_zones.keys()}
        used_seats = set()

        for person in person_detections:
            person_center = bbox_center(person['bbox'])

            closest_seat = None
            closest_dist = float("inf")

            for seat_id, seat_center in seat_centers.items():
                if seat_id in used_seats:
                    continue

                # Optional: require some overlap to be eligible
                if not is_object_in_seat(person['bbox'], seat_zones[seat_id], 'any_overlap'):
                    continue

                d = distance(person_center, seat_center)
                if d < closest_dist:
                    closest_dist = d
                    closest_seat = seat_id

            if closest_seat is not None:
                seats_with_person[closest_seat].append(person)
                used_seats.add(closest_seat)
        
        # Phase 2: Assign objects (priority ke seats dengan person)
        assigned_objects = set()  # Track objek yang sudah di-assign
        seat_objects = {seat_id: [] for seat_id in seat_zones.keys()}
        
        # Priority 1: Seats with persons get their objects first
        for seat_id, seat_bbox in seat_zones.items():
            if len(seats_with_person[seat_id]) > 0:
                for idx, obj in enumerate(object_detections):
                    if idx not in assigned_objects:
                        if is_object_in_seat(obj['bbox'], seat_bbox, 'any_overlap'):
                            seat_objects[seat_id].append(obj)
                            assigned_objects.add(idx)
        
        # Priority 2: Empty seats get remaining objects
        for seat_id, seat_bbox in seat_zones.items():
            if len(seats_with_person[seat_id]) == 0:
                for idx, obj in enumerate(object_detections):
                    if idx not in assigned_objects:
                        if is_object_in_seat(obj['bbox'], seat_bbox, 'any_overlap'):
                            seat_objects[seat_id].append(obj)
                            assigned_objects.add(idx)

        # ======================================================
        # Phase 4 — Produce final seat_statuses
        # ======================================================
        seat_statuses = {}
        
        for seat_id in seat_zones.keys():
            all_objects = seats_with_person[seat_id] + seat_objects[seat_id]
            has_person = len(seats_with_person[seat_id]) > 0
            
            if has_person:
                status = STATUS_OCCUPIED
                reason = "Person detected"
            elif len(seat_objects[seat_id]) > 0:
                status = STATUS_ON_HOLD
                reason = "Objects detected, no person"
            else:
                status = STATUS_EMPTY
                reason = "No objects detected"
            
            seat_statuses[seat_id] = {
                'status': status,
                'detected_objects': [
                    {
                        'class': det['class_name'],
                        'confidence': det['confidence'],
                        'bbox': det['bbox']
                    }
                    for det in all_objects
                ],
                'reason': reason
            }
        
        return seat_statuses
    
    def process_frame(self, frame, seat_zones):
        """
        Complete detection pipeline untuk single frame
        
        Args:
            frame: Input frame (BGR)
            seat_zones: Dict of seat zones
        
        Returns:
            tuple: (all_detections, seat_statuses)
        """
        # 1. Detect objects
        all_detections = self.detect_objects(frame)
        
        # 2. Filter background objects
        all_detections = self.filter_background_objects(all_detections, seat_zones)
        
        # 3. Map to seats
        seat_statuses = self.map_detections_to_seats(all_detections, seat_zones)
        
        return all_detections, seat_statuses