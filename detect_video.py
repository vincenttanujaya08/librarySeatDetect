import cv2
import argparse
import time
from pathlib import Path
from src.detector import SeatDetector
from src.utils import *
from src.config import *


def main(video_path, seat_zones_path=SEAT_ZONES_PATH, output_dir=OUTPUT_DIR, 
         skip_frames=1, display=True, save_video=True):
    """Main detection pipeline for video"""
    
    # Create output directories
    create_output_directories()
    
    # Load video
    print(f"\nLoading video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"✗ Error: Could not open video from {video_path}")
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Video loaded:")
    print(f"  - Resolution: {width}x{height}")
    print(f"  - FPS: {fps}")
    print(f"  - Total frames: {total_frames}")
    print(f"  - Duration: {total_frames/fps:.2f} seconds")
    
    # Load seat zones
    print(f"\nLoading seat zones: {seat_zones_path}")
    seat_zones = load_seat_zones(seat_zones_path)
    print(f"✓ Loaded {len(seat_zones)} seat zones: {list(seat_zones.keys())}")
    
    # Initialize detector
    print("\nInitializing detector...")
    detector = SeatDetector()
    
    # Setup video writer if saving
    video_writer = None
    if save_video:
        video_name = Path(video_path).stem
        output_video_path = Path(ANNOTATED_DIR) / f"{video_name}_annotated.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(
            str(output_video_path), 
            fourcc, 
            fps // skip_frames,  # Adjust FPS based on frame skipping
            (width, height)
        )
        print(f"✓ Output video will be saved to: {output_video_path}")
    
    # Process video
    print(f"\nProcessing video (skipping every {skip_frames} frames)...")
    print("Press 'q' to quit, 'p' to pause/resume")
    
    frame_count = 0
    processed_count = 0
    paused = False
    start_time = time.time()
    
    while True:
        if not paused:
            ret, frame = cap.read()
            
            if not ret:
                print("\n✓ End of video reached")
                break
            
            frame_count += 1
            
            # Skip frames for performance
            if frame_count % skip_frames != 0:
                continue
            
            processed_count += 1
            
            # Process frame
            all_detections, seat_statuses = detector.process_image(frame, seat_zones)
            
            # Visualize results
            vis_frame = visualize_results(frame, seat_zones, seat_statuses, all_detections)
            
            # Add frame info
            elapsed_time = time.time() - start_time
            processing_fps = processed_count / elapsed_time if elapsed_time > 0 else 0
            
            info_text = [
                f"Frame: {frame_count}/{total_frames}",
                f"Processing FPS: {processing_fps:.1f}",
                f"Occupied: {sum(1 for s in seat_statuses.values() if s['status'] == 'occupied')}/{len(seat_zones)}"
            ]
            
            y_offset = 30
            for text in info_text:
                cv2.putText(vis_frame, text, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 30
            
            # Save frame to video
            if video_writer is not None:
                video_writer.write(vis_frame)
            
            # Display frame
            if display:
                # Create named window with resizable property
                cv2.namedWindow('Library Seat Detection - Video', cv2.WINDOW_NORMAL)
                cv2.imshow('Library Seat Detection - Video', vis_frame)
                # cv2.resizeWindow('Library Seat Detection - Live', int(width * 0.5), int(height * 0.5))
            
            # Print progress
            if processed_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames) - "
                      f"Processing FPS: {processing_fps:.1f}")
        
        # Handle keyboard input
        if display:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n✗ User interrupted")
                break
            elif key == ord('p'):
                paused = not paused
                print(f"\n{'⏸ Paused' if paused else '▶ Resumed'}")
    
    # Cleanup
    cap.release()
    if video_writer is not None:
        video_writer.release()
        print(f"\n✓ Video saved successfully")
    
    if display:
        cv2.destroyAllWindows()
    
    # Final statistics
    elapsed_time = time.time() - start_time
    print(f"\n{'='*50}")
    print("Processing Summary:")
    print(f"  - Total frames: {frame_count}")
    print(f"  - Processed frames: {processed_count}")
    print(f"  - Total time: {elapsed_time:.2f} seconds")
    print(f"  - Average processing FPS: {processed_count/elapsed_time:.2f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Library Seat Detection System - Video')
    parser.add_argument('--video', type=str, required=True,
                        help='Path to input video file')
    parser.add_argument('--zones', type=str, default=SEAT_ZONES_PATH,
                        help='Path to seat zones JSON file')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR,
                        help='Output directory')
    parser.add_argument('--skip-frames', type=int, default=1,
                        help='Process every Nth frame (default: 1, process all frames)')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable video display (faster processing)')
    parser.add_argument('--no-save', action='store_true',
                        help='Do not save output video')
    
    args = parser.parse_args()
    
    main(
        args.video, 
        args.zones, 
        args.output,
        args.skip_frames,
        display=not args.no_display,
        save_video=not args.no_save
    )