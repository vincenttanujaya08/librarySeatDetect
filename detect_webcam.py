import cv2
import argparse
import time
from pathlib import Path
from src.detector import SeatDetector
from src.utils import *
from src.config import *


def main(camera_source=0, seat_zones_path=SEAT_ZONES_PATH, 
         skip_frames=2, save_snapshots=True):
    """Main detection pipeline for real-time webcam/IP camera"""
    
    # Create output directories
    create_output_directories()
    
    # Setup camera
    print(f"\nConnecting to camera: {camera_source}")
    
    # For IP Webcam, the URL format is typically:
    # http://[IP_ADDRESS]:8080/video
    # Example: http://192.168.1.100:8080/video
    
    cap = cv2.VideoCapture(camera_source)
    
    # Set buffer size to 1 to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print(f"✗ Error: Could not connect to camera")
        print("\nFor IP Webcam:")
        print("  1. Install 'IP Webcam' app on your phone")
        print("  2. Start the server in the app")
        print("  3. Use URL: http://[PHONE_IP]:8080/video")
        print("  Example: python detect_webcam.py --source http://192.168.100.107:8080/video")
        return
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Camera connected:")
    print(f"  - Resolution: {width}x{height}")
    
    # Create resizable window and set initial size to fit screen better
    cv2.namedWindow('Library Seat Detection - Live', cv2.WINDOW_NORMAL)
   
    cv2.resizeWindow('Library Seat Detection - Live', int(width * 0.5), int(height * 0.5))
    
    # Load seat zones
    print(f"\nLoading seat zones: {seat_zones_path}")
    seat_zones = load_seat_zones(seat_zones_path)
    print(f"✓ Loaded {len(seat_zones)} seat zones: {list(seat_zones.keys())}")
    
    # Initialize detector
    print("\nInitializing detector...")
    detector = SeatDetector()
    
    # Create snapshot directory
    if save_snapshots:
        snapshot_dir = Path(OUTPUT_DIR) / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
    
    # Process stream
    print("\n" + "="*50)
    print("REAL-TIME DETECTION STARTED")
    print("="*50)
    print("Controls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to save snapshot")
    print("  - Press 'p' to pause/resume")
    print("  - Press 'r' to reset FPS counter")
    print("="*50 + "\n")
    
    frame_count = 0
    processed_count = 0
    paused = False
    start_time = time.time()
    fps_start_time = start_time
    fps_frame_count = 0
    
    while True:
        if not paused:
            ret, frame = cap.read()
            
            if not ret:
                print("\n✗ Error: Failed to grab frame")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Skip frames for better performance
            if frame_count % skip_frames != 0:
                continue
            
            processed_count += 1
            fps_frame_count += 1
            
            # Process frame
            all_detections, seat_statuses = detector.process_image(frame, seat_zones)
            
            # Visualize results
            vis_frame = visualize_results(frame, seat_zones, seat_statuses, all_detections)
            
            # Calculate FPS
            current_time = time.time()
            elapsed = current_time - fps_start_time
            if elapsed > 0:
                fps = fps_frame_count / elapsed
            else:
                fps = 0
            
            # Count occupied seats
            occupied = sum(1 for s in seat_statuses.values() if s['status'] == 'occupied')
            total_seats = len(seat_zones)
            occupancy_rate = (occupied / total_seats * 100) if total_seats > 0 else 0
            
            # Add info overlay
            info_text = [
                f"FPS: {fps:.1f}",
                f"Seats: {occupied}/{total_seats} ({occupancy_rate:.1f}%)",
                f"Detections: {len(all_detections)}",
                f"Status: {'PAUSED' if paused else 'RUNNING'}"
            ]
            
            y_offset = 30
            for i, text in enumerate(info_text):
                # Background rectangle for better readability
                (text_width, text_height), _ = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )
                cv2.rectangle(vis_frame, (5, y_offset - 25), 
                             (15 + text_width, y_offset + 5), 
                             (0, 0, 0), -1)
                
                # Text
                color = (0, 255, 255) if i == 0 else (255, 255, 255)
                cv2.putText(vis_frame, text, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                y_offset += 35
            
            # Display frame
            cv2.imshow('Library Seat Detection - Live', vis_frame)
            
            # Print status every 30 frames
            if processed_count % 30 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] FPS: {fps:.1f} | "
                      f"Occupied: {occupied}/{total_seats} | "
                      f"Detections: {len(all_detections)}")
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n✗ Quitting...")
            break
        elif key == ord('s'):
            # Save snapshot
            if save_snapshots:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                snapshot_path = snapshot_dir / f"snapshot_{timestamp}.jpg"
                cv2.imwrite(str(snapshot_path), vis_frame)
                print(f"\n✓ Snapshot saved: {snapshot_path}")
                
                # Save JSON report
                json_path = snapshot_dir / f"snapshot_{timestamp}.json"
                save_json_report(
                    json_path,
                    f"snapshot_{timestamp}.jpg",
                    seat_zones,
                    seat_statuses,
                    all_detections
                )
                print(f"✓ Report saved: {json_path}\n")
        elif key == ord('p'):
            paused = not paused
            print(f"\n{'⏸ PAUSED' if paused else '▶ RESUMED'}\n")
        elif key == ord('r'):
            # Reset FPS counter
            fps_start_time = time.time()
            fps_frame_count = 0
            print("\n✓ FPS counter reset\n")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Final statistics
    total_time = time.time() - start_time
    print(f"\n{'='*50}")
    print("Session Summary:")
    print(f"  - Total frames captured: {frame_count}")
    print(f"  - Frames processed: {processed_count}")
    print(f"  - Session duration: {total_time:.2f} seconds")
    print(f"  - Average processing FPS: {processed_count/total_time:.2f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Library Seat Detection System - Real-time Webcam/IP Camera',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default webcam
  python detect_webcam.py
  
  # Use IP Webcam app
  python detect_webcam.py --source http://192.168.1.100:8080/video
  
  # Use different webcam
  python detect_webcam.py --source 1
  
  # Faster processing (skip more frames)
  python detect_webcam.py --skip-frames 3
        """
    )
    parser.add_argument('--source', type=str, default='0',
                        help='Camera source (0 for default webcam, URL for IP camera)')
    parser.add_argument('--zones', type=str, default=SEAT_ZONES_PATH,
                        help='Path to seat zones JSON file')
    parser.add_argument('--skip-frames', type=int, default=2,
                        help='Process every Nth frame (default: 2, for better performance)')
    parser.add_argument('--no-snapshots', action='store_true',
                        help='Disable snapshot saving feature')
    
    args = parser.parse_args()
    
    # Convert source to int if it's a number (webcam index)
    try:
        source = int(args.source)
    except ValueError:
        source = args.source
    
    main(
        source,
        args.zones,
        args.skip_frames,
        save_snapshots=not args.no_snapshots
    )