# Library Seat Detection System (Petra Library)

## Overview
The **Library Seat Detection System** is a computer vision system designed to automatically monitor seat availability in a library environment using camera input.

Unlike simple people detection systems, this project distinguishes between:

- seats occupied by a person
- seats temporarily reserved with personal belongings
- seats that are truly empty

This distinction is important for public spaces such as libraries where students often leave items (bags or laptops) to reserve a seat.

The system uses **object detection and spatial seat mapping** to determine the status of each seat in real time.

---

# System Architecture

The system consists of two main components:

1. **Detection Engine (Python + YOLOv8)**
2. **Interactive Web Dashboard**

The overall pipeline is:

```
Camera Image
      ↓
YOLO Object Detection
      ↓
Seat Zone Mapping
      ↓
Seat Status Classification
      ↓
JSON Output
      ↓
Web Dashboard Visualization
```

---

# Detection Engine (Python + YOLOv8)

The backend detection system is implemented in Python and located in the `src/` directory.

Main script:

```
detect_image.py
```

This script runs the seat detection pipeline on images captured from the camera.

---

# System Configuration

Configuration parameters are defined in:

```
src/config.py
```

This file defines the core system behavior.

## Model Configuration

The system uses:

```
yolov8s.pt
```

The **YOLOv8 small model** is selected because it provides a good balance between:

- detection accuracy
- inference speed

This makes it suitable for near real-time monitoring.

---

## Target Detection Classes

The system focuses on detecting only objects relevant to seat occupancy:

- Person
- Backpack
- Laptop
- Book

These objects represent typical indicators of seat usage in a library.

---

## Seat Status Categories

Each seat is classified into three possible states:

**OCCUPIED**
- a person is detected in the seat zone
- shown as red in the web dashboard

**ON-HOLD**
- no person detected
- personal belongings present (bag, laptop, book)
- indicates a temporarily reserved seat

**EMPTY**
- no person and no belongings detected
- seat is available

---

# Seat Detection Logic

The core detection pipeline is implemented in:

```
src/detector.py
```

The `SeatDetector` class processes images through several stages.

---

## 1. Object Detection

The YOLO model detects objects within the image.

Each detection contains:

- class label
- confidence score
- bounding box coordinates

Different confidence thresholds are applied depending on the object.

Example:

- Books use a **lower confidence threshold (0.1)** because they are often small and harder to detect.

---

## 2. Background Filtering

Objects detected outside the relevant seating area are filtered out.

This prevents false detections such as:

- people walking in the background
- objects located far away from the tables

A margin is applied around each seat zone to limit valid detections.

---

## 3. Seat Assignment Logic

This is the most critical component of the system.

Each detected object is matched against predefined seat zones.

The system then determines the seat status using priority rules.

### Priority 1 — Person Detected

If a **person** is detected inside the seat zone:

```
Seat Status = OCCUPIED
```

This indicates that the seat is actively being used.

---

### Priority 2 — Belongings Detected

If no person is detected but personal items are present:

- backpack
- laptop
- book

Then:

```
Seat Status = ON-HOLD
```

This indicates that someone has reserved the seat temporarily.

---

### Priority 3 — No Objects Detected

If neither a person nor belongings are detected:

```
Seat Status = EMPTY
```

This means the seat is available.

---

# Utility Functions

Helper functions are located in:

```
src/utils.py
```

These utilities support the main detection pipeline.

---

## Intersection over Union (IOU)

IOU is used to measure the overlap between:

- object detection bounding boxes
- predefined seat zones

Formula:

```
IOU = Area of Overlap / Area of Union
```

If the IOU exceeds a threshold, the object is considered to belong to that seat zone.

---

## Visualization Tools

OpenCV is used to visualize detection results.

The system draws:

- bounding boxes
- seat zone boundaries
- seat status labels

These annotated images are useful for debugging and verification.

---

# Seat Zone Configuration

Seat coordinates are stored in:

```
data/seat_zones.json
```

Each seat has predefined coordinates:

```
x1, y1, x2, y2
```

Example zones:

- a1
- a2
- a3
- b1
- b2
- b3

This **static seat mapping approach** ensures accurate monitoring by focusing only on known seating areas.

---

# Web Dashboard

The frontend provides a real-time visualization of seat availability.

Location:

```
Web/frontend/
```

---

## User Interface

The main interface is:

```
index.html
```

It displays a simplified library map showing seat positions:

```
T1  T2  T3
B1  B2  B3
```

At the top of the dashboard, summary cards display:

- total occupied seats
- seats on hold
- available seats

---

## Frontend Logic

Frontend logic is implemented in:

```
Web/frontend/js/main.js
```

This script handles:

- data updates
- seat status rendering
- interaction logic

---

## Status Mapping

Backend numeric codes are converted into readable seat states.

Example mapping:

```
1 → OCCUPIED
2 → ON-HOLD
3 → EMPTY
```

---

## Real-Time Simulation

The function:

```
runUpdateStep()
```

runs every second to simulate real-time seat updates using:

```
status_simulasi.json
```

This allows testing the dashboard without requiring a live camera feed.

---

## Seat Activity Log

When a seat status changes to **OCCUPIED**, the system records:

- seat ID
- timestamp

Users can click on a seat in the dashboard to view its history.

---

# Full System Workflow

The complete system workflow is as follows:

1. Camera captures an image of the library seating area.

2. The detection engine loads seat coordinates from `seat_zones.json`.

3. YOLO performs object detection on the image.

4. Detected objects are matched to seat zones.

5. The system determines seat status using assignment logic.

6. Results are saved as a JSON report.

7. Annotated images are stored in the `outputs/` directory.

8. The web dashboard reads the JSON data and updates seat visualization.

---

# Key Features

- AI-based seat occupancy detection
- differentiation between occupied and reserved seats
- predefined seat zone mapping for accuracy
- visual verification using bounding boxes
- interactive web dashboard
- seat activity logging

---

# Limitations

Current limitations include:

- dependency on camera angle and lighting
- static seat zone configuration
- limited object classes

---

# Future Improvements

Possible future enhancements include:

- automatic seat zone detection
- multi-camera support
- real-time video processing
- occupancy prediction analytics
- integration with library reservation systems

---

# Conclusion

This project demonstrates how **computer vision can be applied to space management in public facilities**.

By combining object detection with seat zone mapping and smart status classification, the system provides a practical solution for monitoring seat availability in libraries.
