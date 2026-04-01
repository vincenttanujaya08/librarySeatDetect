"""
Seat Zones Verification Tool
Captures frame and overlays seat zones to verify positioning
Saves screenshot for inspection
"""

import cv2
import mss
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime

class ZoneVerifier:
    def __init__(self):
        self.roi = None
        self.seat_zones = None
        self.colors = {
            't1': (255, 0, 0),      # Blue
            't2': (0, 255, 0),      # Green
            't3': (0, 0, 255),      # Red
            'b1': (255, 255, 0),    # Cyan
            'b2': (255, 0, 255),    # Magenta
            'b3': (0, 255, 255),    # Yellow
        }
    
    def load_config(self):
        """Load ROI and seat zones configuration"""
        print("\n" + "="*60)
        print("  LOADING CONFIGURATION")
        print("="*60)
        
        # Load ROI
        roi_path = 'config/monitor_roi.json'
        if not os.path.exists(roi_path):
            print("❌ Error: config/monitor_roi.json not found!")
            print("   Run: python setup_roi.py")
            return False
        
        with open(roi_path, 'r') as f:
            self.roi = json.load(f)
        print(f"✅ ROI loaded: {self.roi['width']}x{self.roi['height']}")
        
        # Load seat zones
        zones_path = 'data/seat_zones.json'
        if not os.path.exists(zones_path):
            print("❌ Error: data/seat_zones.json not found!")
            print("   Run: python setup_seat_zones.py")
            return False
        
        with open(zones_path, 'r') as f:
            self.seat_zones = json.load(f)
        print(f"✅ Seat zones loaded: {len(self.seat_zones)} zones")
        
        return True
    
    def capture_frame(self):
        """Capture current frame from ROI"""
        sct = mss.mss()
        img = np.array(sct.grab(self.roi))
        frame = img[:, :, :3]  # BGRA -> BGR
        return frame
    
    def draw_zones(self, frame):
        """Draw all seat zones on frame with labels"""
        vis_frame = frame.copy()
        
        for seat_id, coords in self.seat_zones.items():
            x1, y1 = coords['x1'], coords['y1']
            x2, y2 = coords['x2'], coords['y2']
            
            # Get color for this seat
            color = self.colors.get(seat_id.lower(), (128, 128, 128))
            
            # Draw thick rectangle
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 4)
            
            # Calculate zone center for label
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Draw seat ID at center
            label = seat_id.upper()
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.5
            thickness = 3
            
            # Get text size
            (text_w, text_h), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )
            
            # Draw background rectangle for text
            bg_x1 = center_x - text_w // 2 - 10
            bg_y1 = center_y - text_h // 2 - 10
            bg_x2 = center_x + text_w // 2 + 10
            bg_y2 = center_y + text_h // 2 + 10
            
            cv2.rectangle(vis_frame, (bg_x1, bg_y1), (bg_x2, bg_y2), 
                         color, -1)
            
            # Draw white text
            text_x = center_x - text_w // 2
            text_y = center_y + text_h // 2
            cv2.putText(vis_frame, label, (text_x, text_y), 
                       font, font_scale, (255, 255, 255), thickness)
            
            # Draw corner indicators
            corner_size = 20
            # Top-left
            cv2.line(vis_frame, (x1, y1), (x1 + corner_size, y1), color, 3)
            cv2.line(vis_frame, (x1, y1), (x1, y1 + corner_size), color, 3)
            # Top-right
            cv2.line(vis_frame, (x2, y1), (x2 - corner_size, y1), color, 3)
            cv2.line(vis_frame, (x2, y1), (x2, y1 + corner_size), color, 3)
            # Bottom-left
            cv2.line(vis_frame, (x1, y2), (x1 + corner_size, y2), color, 3)
            cv2.line(vis_frame, (x1, y2), (x1, y2 - corner_size), color, 3)
            # Bottom-right
            cv2.line(vis_frame, (x2, y2), (x2 - corner_size, y2), color, 3)
            cv2.line(vis_frame, (x2, y2), (x2, y2 - corner_size), color, 3)
        
        # Add title
        title = "Seat Zones Verification"
        cv2.putText(vis_frame, title, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(vis_frame, timestamp, (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return vis_frame
    
    def save_screenshot(self, frame, filename=None):
        """Save verification screenshot"""
        # Create output directory
        Path('outputs/zone_verification').mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"outputs/zone_verification/zones_{timestamp}.jpg"
        
        cv2.imwrite(filename, frame)
        print(f"📸 Screenshot saved: {filename}")
        
        return filename
    
    def print_zone_info(self):
        """Print detailed zone information"""
        print("\n" + "="*60)
        print("  SEAT ZONES INFORMATION")
        print("="*60)
        
        for seat_id, coords in self.seat_zones.items():
            x1, y1 = coords['x1'], coords['y1']
            x2, y2 = coords['x2'], coords['y2']
            width = x2 - x1
            height = y2 - y1
            
            print(f"\n[{seat_id.upper()}]")
            print(f"  Position: ({x1}, {y1}) to ({x2}, {y2})")
            print(f"  Size: {width}x{height} pixels")
            print(f"  Center: ({(x1+x2)//2}, {(y1+y2)//2})")
    
    def run_continuous(self):
        """Run continuous verification with live preview"""
        print("\n" + "="*60)
        print("  CONTINUOUS VERIFICATION MODE")
        print("="*60)
        print("\nControls:")
        print("  's' - Save screenshot")
        print("  'q' - Quit")
        print("  Any other key - Refresh frame")
        print("\n" + "="*60 + "\n")
        
        sct = mss.mss()
        
        while True:
            # Capture frame
            img = np.array(sct.grab(self.roi))
            frame = img[:, :, :3]
            
            # Draw zones
            vis_frame = self.draw_zones(frame)
            
            # Add instructions
            cv2.putText(vis_frame, "Press 's' to save | 'q' to quit", 
                       (20, vis_frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Show frame
            cv2.imshow('Zone Verification - Live Preview', vis_frame)
            
            # Handle key press
            key = cv2.waitKey(100) & 0xFF
            
            if key == ord('q'):
                print("\n✅ Verification complete")
                break
            elif key == ord('s'):
                self.save_screenshot(vis_frame)
                print("   Screenshot saved!")
        
        cv2.destroyAllWindows()
    
    def run_single(self):
        """Run single verification with screenshot"""
        print("\n" + "="*60)
        print("  SINGLE VERIFICATION")
        print("="*60)
        
        # Capture frame
        print("\n📸 Capturing frame...")
        frame = self.capture_frame()
        
        # Draw zones
        print("🎨 Drawing seat zones...")
        vis_frame = self.draw_zones(frame)
        
        # Save screenshot
        print("💾 Saving screenshot...")
        filepath = self.save_screenshot(vis_frame)
        
        # Print zone info
        self.print_zone_info()
        
        # Show preview
        print("\n" + "="*60)
        print("  PREVIEW")
        print("="*60)
        print("\n📺 Showing preview...")
        print("   Press any key to close\n")
        
        cv2.imshow('Zone Verification', vis_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        print("\n✅ Verification complete!")
        print(f"   Screenshot: {filepath}\n")


def main():
    """Main entry point"""
    verifier = ZoneVerifier()
    
    print("\n" + "="*60)
    print("  PETRA LIBRARY - SEAT ZONES VERIFICATION TOOL")
    print("="*60)
    
    # Load configuration
    if not verifier.load_config():
        print("\n❌ Cannot proceed without configuration\n")
        return
    
    # Ask user for mode
    print("\n" + "="*60)
    print("  SELECT MODE")
    print("="*60)
    print("\n1. Single verification (capture + save + show)")
    print("2. Continuous preview (live stream with zones)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '2':
        verifier.run_continuous()
    else:
        verifier.run_single()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()