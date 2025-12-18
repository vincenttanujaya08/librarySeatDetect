"""
Utility Functions
Helper functions untuk loading, visualization, calculations
"""

import json
import cv2
import numpy as np
from src.config import *


def load_seat_zones(json_path):
    """
    Load seat zones from JSON file
    
    Args:
        json_path: Path to seat_zones.json
    
    Returns:
        dict: {seat_id: [x1, y1, x2, y2]}
    """
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
    
    Args:
        box1: [x1, y1, x2, y2]
        box2: [x1, y1, x2, y2]
    
    Returns:
        float: IoU value (0-1)
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


def is_object_in_seat(obj_bbox, seat_bbox, method='any_overlap'):
    """
    Check if object is in seat zone
    
    Args:
        obj_bbox: [x1, y1, x2, y2] of detected object
        seat_bbox: [x1, y1, x2, y2] of seat zone
        method: 'iou', 'center', or 'any_overlap'
    
    Returns:
        bool: True if object is in seat
    """
    if method == 'iou':
        return calculate_iou(obj_bbox, seat_bbox) > IOU_THRESHOLD
    
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


def get_status_color(status):
    """
    Get color for status visualization
    
    Args:
        status: STATUS_OCCUPIED, STATUS_ON_HOLD, or STATUS_EMPTY
    
    Returns:
        tuple: BGR color
    """
    if status == STATUS_OCCUPIED:
        return COLOR_OCCUPIED
    elif status == STATUS_ON_HOLD:
        return COLOR_ON_HOLD
    else:
        return COLOR_EMPTY


def draw_bounding_box(image, box, label, color, thickness=2):
    """
    Draw bounding box with label on image
    
    Args:
        image: Input image
        box: [x1, y1, x2, y2]
        label: Label text
        color: BGR color
        thickness: Line thickness
    
    Returns:
        image: Image with bounding box drawn
    """
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