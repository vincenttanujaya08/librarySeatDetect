import cv2
import argparse
from pathlib import Path
from src.detector import SeatDetector
from src.utils import *
from src.config import *


def main(image_path, seat_zones_path=SEAT_ZONES_PATH, output_dir=OUTPUT_DIR):
    """Main detection pipeline for single image"""
    
    # Create output directories
    create_output_directories()
    
    # Load image
    print(f"\nLoading image: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"✗ Error: Could not load image from {image_path}")
        return
    
    h, w = image.shape[:2]
    print(f"✓ Image loaded: {w}x{h} pixels")
    
    # Load seat zones
    print(f"\nLoading seat zones: {seat_zones_path}")
    seat_zones = load_seat_zones(seat_zones_path)
    print(f"✓ Loaded {len(seat_zones)} seat zones: {list(seat_zones.keys())}")
    
    # Initialize detector
    print("\nInitializing detector...")
    detector = SeatDetector()
    
    # Process image
    print("\nRunning detection...")
    all_detections, seat_statuses = detector.process_image(image, seat_zones)
    print(f"✓ Detection complete: {len(all_detections)} objects detected")
    
    # Visualize results
    print("\nGenerating visualization...")
    vis_image = visualize_results(image, seat_zones, seat_statuses, all_detections)
    
    # Save annotated image
    image_name = Path(image_path).name
    output_image_path = Path(ANNOTATED_DIR) / f"{Path(image_name).stem}_annotated.jpg"
    cv2.imwrite(str(output_image_path), vis_image)
    print(f"✓ Annotated image saved: {output_image_path}")
    
    # Save JSON report
    json_output_path = Path(OUTPUT_DIR) / "seat_status.json"
    report = save_json_report(
        json_output_path,
        image_name,
        seat_zones,
        seat_statuses,
        all_detections
    )
    print(f"✓ JSON report saved: {json_output_path}")
    
    # Print terminal report
    print_terminal_report(report)
    
    # Display result (optional)
    print("Press any key to close the window...")
    cv2.imshow('Library Seat Detection', vis_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Library Seat Detection System')
    parser.add_argument('--image', type=str, required=True,
                        help='Path to input image')
    parser.add_argument('--zones', type=str, default=SEAT_ZONES_PATH,
                        help='Path to seat zones JSON file')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR,
                        help='Output directory')
    
    args = parser.parse_args()
    
    main(args.image, args.zones, args.output)