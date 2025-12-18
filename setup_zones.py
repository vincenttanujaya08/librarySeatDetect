"""
Petra Library Seat Detection - Seat Zones Setup
Setup seat zones only (ROI sudah hardcoded di config.py)

Usage: python setup_zones.py
"""

import cv2
import mss
import numpy as np
import json
from pathlib import Path
import sys

# Import ROI dari config
sys.path.append('.')
from src.config import MONITOR_ROI


class SeatZonesSetup:
    def __init__(self):
        self.roi = MONITOR_ROI
        self.seat_zones = {}
        self.seat_ids = ["T1", "T2", "T3", "B1", "B2", "B3"]
        self.colors = [
            (255, 0, 0),    # Blue
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]
        self.base_frame = None
    
    def print_header(self, title):
        """Print fancy header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    def capture_base_frame(self):
        """Capture frozen frame from hardcoded ROI"""
        print("\n📸 Capturing frame from hardcoded ROI...")
        print(f"   ROI: {self.roi['width']}x{self.roi['height']} at ({self.roi['left']}, {self.roi['top']})")
        
        sct = mss.mss()
        img = np.array(sct.grab(self.roi))
        self.base_frame = img[:, :, :3].copy()  # BGRA -> BGR
        
        # Show preview
        preview = self.base_frame.copy()
        cv2.putText(preview, "Frozen frame captured - Press any key", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow("Frozen Frame", preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def draw_zones_on_frame(self, frame, zones):
        """Draw existing zones as overlay"""
        vis = frame.copy()
        
        for seat_id, coords in zones.items():
            x1, y1 = int(coords["x1"]), int(coords["y1"])
            x2, y2 = int(coords["x2"]), int(coords["y2"])
            
            # Find color
            try:
                idx = self.seat_ids.index(seat_id.upper())
                color = self.colors[idx]
            except:
                color = (128, 128, 128)
            
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 3)
            
            # Draw label
            label = seat_id.upper()
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, th), _ = cv2.getTextSize(label, font, 0.9, 2)
            
            y_top = max(0, y1 - th - 10)
            cv2.rectangle(vis, (x1, y_top), (x1 + tw + 10, y1), color, -1)
            cv2.putText(vis, label, (x1 + 5, y1 - 5), font, 0.9, (255, 255, 255), 2)
        
        return vis
    
    def setup_seat_zones(self):
        """Mark 6 seat positions"""
        self.print_header("MARK SEAT POSITIONS")
        
        print("🪑 Instructions:")
        print("  You will mark 6 seat positions one by one:")
        print("  - T1, T2, T3 (Top row, left to right)")
        print("  - B1, B2, B3 (Bottom row, left to right)")
        print()
        print("  For each seat:")
        print("  1. Draw a rectangle around the seat area")
        print("  2. Press ENTER to confirm")
        print("  3. Press C to redraw")
        print("  4. Press ESC to skip")
        print()
        
        input("Press ENTER to start...")
        
        # Capture frozen frame once
        self.capture_base_frame()
        
        # Mark each seat
        for idx, seat_id in enumerate(self.seat_ids, start=1):
            print(f"\n[{idx}/6] Marking seat: {seat_id}")
            
            # Use frozen frame with overlay
            frame = self.base_frame.copy()
            if self.seat_zones:
                frame = self.draw_zones_on_frame(frame, self.seat_zones)
            
            instruction = f"Draw rectangle for {seat_id} - ENTER confirm | C redraw | ESC skip"
            cv2.putText(frame, instruction, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            roi = cv2.selectROI(f"Setup {seat_id}", frame, 
                               showCrosshair=True, fromCenter=False)
            cv2.destroyAllWindows()
            
            x, y, w, h = roi
            if w == 0 or h == 0:
                print(f"   ⚠️  Skipped {seat_id}")
                continue
            
            self.seat_zones[seat_id.lower()] = {
                "x1": int(x),
                "y1": int(y),
                "x2": int(x + w),
                "y2": int(y + h),
            }
            print(f"   ✅ {seat_id} marked: {w}x{h} at ({x}, {y})")
        
        print(f"\n✅ Setup complete!")
        print(f"   Total zones defined: {len(self.seat_zones)}")
        
        return len(self.seat_zones) > 0
    
    def preview_final(self):
        """Show final preview"""
        if not self.seat_zones:
            print("\n⚠️  No zones defined, skipping preview.")
            return
        
        self.print_header("FINAL PREVIEW")
        
        frame = self.base_frame.copy()
        vis = self.draw_zones_on_frame(frame, self.seat_zones)
        
        cv2.putText(vis, "FINAL PREVIEW - Press any key to save",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        
        cv2.imshow("Final Preview", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def save_config(self):
        """Save seat zones to JSON"""
        self.print_header("SAVING CONFIGURATION")
        
        # Create config directory
        Path('config').mkdir(exist_ok=True)
        
        # Save seat zones
        zones_path = 'config/seat_zones.json'
        with open(zones_path, 'w') as f:
            json.dump(self.seat_zones, f, indent=2)
        print(f"✅ Seat zones saved: {zones_path}")
    
    def print_summary(self):
        """Print setup summary"""
        self.print_header("SETUP COMPLETE")
        
        print("📋 Summary:")
        print(f"   ROI: {self.roi['width']}x{self.roi['height']} (hardcoded)")
        print(f"   Seats defined: {len(self.seat_zones)}")
        print()
        
        print("📁 Config file created:")
        print("   ✅ config/seat_zones.json")
        print()
        
        print("🚀 Next step:")
        print("   Run the detection server:")
        print("   $ python run_server.py")
        print()
    
    def run(self):
        """Main workflow"""
        self.print_header("PETRA LIBRARY SEAT DETECTION - SETUP")
        
        print("Welcome! This tool will guide you through marking 6 seat positions.")
        print(f"ROI is hardcoded: {self.roi['width']}x{self.roi['height']} at ({self.roi['left']}, {self.roi['top']})")
        print()
        
        # Setup seat zones
        if not self.setup_seat_zones():
            print("\n❌ Setup incomplete. No seat zones defined.")
            return
        
        # Preview
        self.preview_final()
        
        # Save
        self.save_config()
        
        # Summary
        self.print_summary()


def main():
    """Entry point"""
    try:
        setup = SeatZonesSetup()
        setup.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        print("👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()