import json
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from src.config import *


def load_seat_zones(json_path):
    """Load seat zones from JSON file"""
    with open(json_path, 'r') as f:
        zones = json.load(f)
    
    # Convert to format: {seat_id: [x1, y1, x2, y2]}
    seat_zones = {}
    for seat_id, coords in zones.items():
        seat_zones[seat_id] = [
            coords['x1'],
            coords['y1'],
            coords['x2'],
            coords['y2']
        ]
    
    return seat_zones


def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union (IoU) between two bounding boxes
    box format: [x1, y1, x2, y2]
    """
    # Intersection coordinates
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    # Intersection area
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    # Union area
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    # IoU
    iou = intersection / union if union > 0 else 0
    
    return iou

def is_object_in_seat(obj_bbox, seat_bbox, method='iou', threshold=0.2):
    """
    Check if object is in seat zone using different methods
    
    Args:
        obj_bbox: [x1, y1, x2, y2] of detected object
        seat_bbox: [x1, y1, x2, y2] of seat zone
        method: 'iou' or 'center' or 'any_overlap'
        threshold: threshold value (for iou method)
    
    Returns:
        bool: True if object is considered in seat
    """
    if method == 'iou':
        return calculate_iou(obj_bbox, seat_bbox) > threshold
    
    elif method == 'center':
        # Check if object center is inside seat zone
        obj_center_x = (obj_bbox[0] + obj_bbox[2]) / 2
        obj_center_y = (obj_bbox[1] + obj_bbox[3]) / 2
        
        return (seat_bbox[0] <= obj_center_x <= seat_bbox[2] and
                seat_bbox[1] <= obj_center_y <= seat_bbox[3])
    
    elif method == 'any_overlap':
        # Check if there's any overlap at all
        x1 = max(obj_bbox[0], seat_bbox[0])
        y1 = max(obj_bbox[1], seat_bbox[1])
        x2 = min(obj_bbox[2], seat_bbox[2])
        y2 = min(obj_bbox[3], seat_bbox[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        return intersection > 0
    
    return False


def determine_seat_status(detections_in_seat):
    """
    Determine seat status based on detected objects
    detections_in_seat: list of detection dicts with 'class_id' and 'confidence'
    """
    person_detected = any(d['class_id'] == CLASS_PERSON for d in detections_in_seat)
    
    if person_detected:
        return STATUS_OCCUPIED
    elif len(detections_in_seat) > 0:
        return STATUS_ON_HOLD
    else:
        return STATUS_EMPTY


def get_status_color(status):
    """Get color for status visualization"""
    if status == STATUS_OCCUPIED:
        return COLOR_OCCUPIED
    elif status == STATUS_ON_HOLD:
        return COLOR_ON_HOLD
    else:
        return COLOR_EMPTY


def draw_bounding_box(image, box, label, color, thickness=2):
    """Draw bounding box with label on image"""
    x1, y1, x2, y2 = map(int, box)
    
    # Draw rectangle
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label background
    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    label_y = max(y1, label_size[1] + 10)
    cv2.rectangle(image, (x1, label_y - label_size[1] - 10), 
                  (x1 + label_size[0], label_y), color, -1)
    
    # Draw label text
    cv2.putText(image, label, (x1, label_y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    return image


def visualize_results(image, seat_zones, seat_statuses, all_detections):
    """
    Visualize detection results on image
    """
    vis_image = image.copy()
    
    # Draw all detections
    for det in all_detections:
        class_id = det['class_id']
        bbox = det['bbox']
        conf = det['confidence']
        
        color = DETECTION_COLORS.get(class_id, (128, 128, 128))
        label = f"{CLASS_NAMES.get(class_id, 'unknown')} {conf:.2f}"
        
        vis_image = draw_bounding_box(vis_image, bbox, label, color, thickness=2)
    
    # Draw seat zones with status
    for seat_id, zone_bbox in seat_zones.items():
        status = seat_statuses.get(seat_id, {}).get('status', STATUS_EMPTY)
        color = get_status_color(status)
        
        # Draw seat zone
        x1, y1, x2, y2 = map(int, zone_bbox)
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), COLOR_SEAT_ZONE, 3)
        
        # Draw status label
        label = f"{seat_id.upper()}: {status}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        
        # Position label at top of seat zone
        label_x = x1 + 5
        label_y = y1 + 30
        
        # Draw background for label
        cv2.rectangle(vis_image, 
                      (label_x - 5, label_y - label_size[1] - 5),
                      (label_x + label_size[0] + 5, label_y + 5),
                      color, -1)
        
        # Draw text
        cv2.putText(vis_image, label, (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    return vis_image


def save_json_report(output_path, image_name, seat_zones, seat_statuses, all_detections):
    """Save detection results to JSON file"""
    # Calculate summary
    summary = {
        STATUS_OCCUPIED: 0,
        STATUS_ON_HOLD: 0,
        STATUS_EMPTY: 0
    }
    
    for seat_id, status_data in seat_statuses.items():
        status = status_data['status']
        summary[status] += 1
    
    # Prepare report
    report = {
        "image_name": image_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_seats": len(seat_zones),
        "summary": {
            "occupied": summary[STATUS_OCCUPIED],
            "on_hold": summary[STATUS_ON_HOLD],
            "empty": summary[STATUS_EMPTY]
        },
        "seats": seat_statuses,
        "total_detections": len(all_detections)
    }
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report


def print_terminal_report(report):
    """Print formatted report to terminal"""
    print("\n" + "="*60)
    print("        LIBRARY SEAT DETECTION SYSTEM")
    print("="*60)
    print(f"Image: {report['image_name']}")
    print(f"Timestamp: {report['timestamp']}")
    print("-"*60)
    
    print(f"\nTotal Detections: {report['total_detections']}")
    print("-"*60)
    
    print("\nSeat Status Summary:")
    print("-"*60)
    summary = report['summary']
    print(f"🟢 OCCUPIED:  {summary['occupied']} seats")
    print(f"🟡 ON-HOLD:   {summary['on_hold']} seats")
    print(f"🔴 EMPTY:     {summary['empty']} seats")
    
    print("\n" + "-"*60)
    print("Detailed Status:")
    print("-"*60)
    
    for seat_id, data in report['seats'].items():
        status = data['status']
        
        # Status emoji
        if status == STATUS_OCCUPIED:
            emoji = "🟢"
        elif status == STATUS_ON_HOLD:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        # Objects info
        objects = data['detected_objects']
        if len(objects) > 0:
            obj_info = f"{objects[0]['class']} (conf: {objects[0]['confidence']:.2f})"
        else:
            obj_info = "No objects detected"
        
        print(f"[{seat_id.upper()}] {emoji} {status:10s} - {obj_info}")
    
    print("\n" + "="*60)
    print("✓ Results saved successfully")
    print("="*60 + "\n")


def create_output_directories():
    """Create output directories if they don't exist"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(ANNOTATED_DIR).mkdir(parents=True, exist_ok=True)