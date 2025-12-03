from ultralytics import YOLO
import cv2
import numpy as np
from src.config import *
from src.utils import calculate_iou, determine_seat_status, CLASS_NAMES, is_object_in_seat


class SeatDetector:
    def __init__(self, model_path=YOLO_MODEL):
        """Initialize YOLO detector"""
        print(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.iou_threshold = IOU_THRESHOLD
        print("✓ Model loaded successfully")
    
    def detect_objects(self, image):
        """
        Run YOLO detection on image with class-specific confidence thresholds
        """
        # Run YOLO inference with LOWER threshold first
        results = self.model.predict(
            image,
            classes=DETECT_CLASSES,
            conf=0.10,  # Low threshold to catch all
            verbose=False
        )
        
        # Class-specific confidence thresholds
        class_thresholds = {
            CLASS_PERSON: 0.3,      # Higher for person (reduce false positives)
            CLASS_BACKPACK: 0.25,
            CLASS_LAPTOP: 0.25,
            CLASS_BOOK: 0.1,       # Lower for book (harder to detect on table)
            CLASS_CELL_PHONE: 0.25,
            CLASS_BOTTLE: 0.30,
            CLASS_CUP: 0.30
        }
        
        detections = []
    
    # Parse results
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Get box data
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                
                # Apply class-specific threshold
                min_conf = class_thresholds.get(class_id, 0.25)
                
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
    
    def filter_detections_by_area(self, detections, seat_zones):
        """
        Filter out detections that are far from any seat zone (background objects)
        """
        filtered = []
        
        # Calculate expanded area covering all seats
        all_x1 = min(zone[0] for zone in seat_zones.values())
        all_y1 = min(zone[1] for zone in seat_zones.values())
        all_x2 = max(zone[2] for zone in seat_zones.values())
        all_y2 = max(zone[3] for zone in seat_zones.values())
        
        # Expand by 100 pixels on each side (margin for objects near seats)
        margin = 100
        valid_area = [
            all_x1 - margin,
            all_y1 - margin,
            all_x2 + margin,
            all_y2 + margin
        ]
        
        for det in detections:
            # Check if object center is within valid area
            obj_center_x = (det['bbox'][0] + det['bbox'][2]) / 2
            obj_center_y = (det['bbox'][1] + det['bbox'][3]) / 2
            
            if (valid_area[0] <= obj_center_x <= valid_area[2] and
                valid_area[1] <= obj_center_y <= valid_area[3]):
                filtered.append(det)
        
        return filtered
    
    def map_detections_to_seats(self, detections, seat_zones):
        """
        Map detected objects to seat zones with priority-based assignment
        Priority: Seats with person get their objects first
        Returns dict: {seat_id: {'status': str, 'detected_objects': [...], 'reason': str}}
        """
        # Phase 1: Find which seats have persons
        seats_with_person = {}
        person_detections = []
        object_detections = []
        
        # Separate persons and objects
        for det in detections:
            if det['class_id'] == CLASS_PERSON:
                person_detections.append(det)
            else:
                object_detections.append(det)
        
        # Assign persons to seats
        for seat_id, seat_bbox in seat_zones.items():
            seats_with_person[seat_id] = []
            
            for person in person_detections:
                if is_object_in_seat(person['bbox'], seat_bbox, method='any_overlap'):
                    seats_with_person[seat_id].append(person)
        
        # Phase 2: Assign objects with priority
        # Priority 1: Assign objects to seats that have persons
        assigned_objects = set()  # Track which objects have been assigned
        seat_objects = {seat_id: [] for seat_id in seat_zones.keys()}
        
        for seat_id, seat_bbox in seat_zones.items():
            # If seat has person, assign all overlapping objects to this seat
            if len(seats_with_person[seat_id]) > 0:
                for idx, obj in enumerate(object_detections):
                    if idx not in assigned_objects:
                        if is_object_in_seat(obj['bbox'], seat_bbox, method='any_overlap'):
                            seat_objects[seat_id].append(obj)
                            assigned_objects.add(idx)
        
        # Priority 2: Assign remaining objects to empty seats
        for seat_id, seat_bbox in seat_zones.items():
            # Only for seats without persons
            if len(seats_with_person[seat_id]) == 0:
                for idx, obj in enumerate(object_detections):
                    if idx not in assigned_objects:
                        # Use any_overlap for all objects (including books)
                        if is_object_in_seat(obj['bbox'], seat_bbox, method='any_overlap'):
                            seat_objects[seat_id].append(obj)
                            assigned_objects.add(idx)
        
        # Phase 3: Determine status for each seat
        seat_statuses = {}
        
        print("\n" + "="*60)
        print("SEAT ASSIGNMENT DEBUG INFO")
        print("="*60)
        
        for seat_id in seat_zones.keys():
            all_objects_in_seat = seats_with_person[seat_id] + seat_objects[seat_id]
            
            # DEBUG: Print assignment info
            print(f"\n[{seat_id.upper()}]")
            print(f"  Persons detected: {len(seats_with_person[seat_id])}")
            print(f"  Objects detected: {len(seat_objects[seat_id])}")
            if len(seat_objects[seat_id]) > 0:
                for obj in seat_objects[seat_id]:
                    print(f"    → {obj['class_name']} (confidence: {obj['confidence']:.2f})")
            
            # Determine status
            has_person = len(seats_with_person[seat_id]) > 0
            
            if has_person:
                status = STATUS_OCCUPIED
                reason = "Person detected in seat zone"
            elif len(seat_objects[seat_id]) > 0:
                status = STATUS_ON_HOLD
                reason = "Object detected, no person present"
            else:
                status = STATUS_EMPTY
                reason = "No objects or person detected"
            
            print(f"  → Final Status: {status}")
            
            # Store result
            seat_statuses[seat_id] = {
                'status': status,
                'detected_objects': [
                    {
                        'class': det['class_name'],
                        'confidence': det['confidence'],
                        'bbox': det['bbox']
                    }
                    for det in all_objects_in_seat
                ],
                'reason': reason
            }
        
        print("\n" + "="*60 + "\n")
        
        return seat_statuses
    
    def process_image(self, image, seat_zones):
        """
        Complete detection pipeline for an image
        Returns: (all_detections, seat_statuses)
        """
        # Run detection
        all_detections = self.detect_objects(image)
        
        # Filter out background objects (like books on shelf)
        all_detections = self.filter_detections_by_area(all_detections, seat_zones)
        
        # Map to seats
        seat_statuses = self.map_detections_to_seats(all_detections, seat_zones)
        
        return all_detections, seat_statuses