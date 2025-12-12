"""
Smart Launcher for Petra Library Seat Detection System
Automatically checks prerequisites and guides user through setup
"""

import os
import sys
import time
import webbrowser
import threading
import subprocess
from pathlib import Path

class SystemLauncher:
    def __init__(self):
        self.roi_path = 'config/monitor_roi.json'
        self.zones_path = 'data/seat_zones.json'
        self.server_running = False
        
    def print_header(self, title):
        """Print fancy header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")
    
    def print_step(self, step_num, total, message):
        """Print step indicator"""
        print(f"[Step {step_num}/{total}] {message}")
    
    def check_roi_exists(self):
        """Check if ROI configuration exists"""
        return os.path.exists(self.roi_path)
    
    def check_zones_exist(self):
        """Check if seat zones configuration exists"""
        return os.path.exists(self.zones_path)
    
    def run_setup_roi(self):
        """Run ROI setup script"""
        self.print_header("SETUP: Monitor Area (ROI)")
        print("📸 You need to select the area to monitor")
        print("   This is usually your Photo Booth or Zoom window")
        print("\nInstructions:")
        print("  1. A screenshot will appear")
        print("  2. Draw a rectangle around the library area")
        print("  3. Press ENTER to confirm\n")
        
        input("Press ENTER to start ROI setup...")
        
        try:
            subprocess.run([sys.executable, 'setup_roi.py'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("\n❌ ROI setup failed!")
            return False
        except KeyboardInterrupt:
            print("\n⚠️  Setup cancelled by user")
            return False
    
    def run_setup_zones(self):
        """Run seat zones setup script"""
        self.print_header("SETUP: Seat Zones")
        print("🪑 You need to mark 6 seat positions")
        print("   Seats: T1, T2, T3 (top row) and B1, B2, B3 (bottom row)")
        print("\nInstructions:")
        print("  1. For each seat, draw a rectangle around it")
        print("  2. Press ENTER to confirm each seat")
        print("  3. Press C to cancel and redraw\n")
        
        input("Press ENTER to start seat zones setup...")
        
        try:
            subprocess.run([sys.executable, 'setup_seat_zones.py'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("\n❌ Seat zones setup failed!")
            return False
        except KeyboardInterrupt:
            print("\n⚠️  Setup cancelled by user")
            return False
    
    def open_browser_delayed(self, url, delay=3):
        """Open browser after delay"""
        time.sleep(delay)
        print(f"\n🌐 Opening browser: {url}")
        webbrowser.open(url)
    
    def print_split_screen_instructions(self):
        """Print instructions for split screen setup"""
        self.print_header("SPLIT SCREEN SETUP")
        print("📺 To view camera and detection side-by-side:")
        print("\n  Windows:")
        print("    1. Open Photo Booth/Camera app")
        print("    2. Press Windows + ← (snap to left)")
        print("    3. Browser will open automatically")
        print("    4. Press Windows + → (snap to right)")
        print("\n  Mac:")
        print("    1. Open Photo Booth/Camera app")
        print("    2. Hover green button → select 'Tile Window to Left'")
        print("    3. Browser will open automatically")
        print("    4. Select browser to tile right")
        print("\n" + "="*70 + "\n")
    
    def start_server(self):
        """Start the detection server"""
        self.print_header("STARTING DETECTION SERVER")
        
        print("🚀 Starting Flask + SocketIO server...")
        print("📡 Server will run on: http://localhost:5000")
        print("\n⏳ Please wait for server to start (3 seconds)...\n")
        
        # Print split screen instructions
        self.print_split_screen_instructions()
        
        # Schedule browser opening
        browser_thread = threading.Thread(
            target=self.open_browser_delayed, 
            args=('http://localhost:5000', 3),
            daemon=True
        )
        browser_thread.start()
        
        # Import and run server
        try:
            print("="*70)
            print("  SERVER LOGS")
            print("="*70 + "\n")
            
            # Import server modules
            from stream_server import app, socketio
            
            # Run server
            socketio.run(app, 
                        host='0.0.0.0', 
                        port=5000, 
                        debug=False,
                        allow_unsafe_werkzeug=True)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Server stopped by user")
            print("✅ Shutdown complete\n")
        except Exception as e:
            print(f"\n❌ Server error: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main launcher workflow"""
        self.print_header("PETRA LIBRARY SEAT DETECTION SYSTEM - LAUNCHER")
        
        print("👋 Welcome! This launcher will guide you through setup")
        print("   and start the detection system automatically.\n")
        
        # Step 1: Check ROI
        self.print_step(1, 3, "Checking Monitor ROI configuration...")
        
        if not self.check_roi_exists():
            print("   ⚠️  ROI not configured")
            if not self.run_setup_roi():
                print("\n❌ Cannot proceed without ROI configuration")
                return
        else:
            print("   ✅ ROI already configured")
        
        # Step 2: Check Seat Zones
        self.print_step(2, 3, "Checking Seat Zones configuration...")
        
        if not self.check_zones_exist():
            print("   ⚠️  Seat zones not configured")
            if not self.run_setup_zones():
                print("\n❌ Cannot proceed without seat zones configuration")
                return
        else:
            print("   ✅ Seat zones already configured")
            print("   📸 Verifying zones...")
            
            # Run verification
            try:
                subprocess.run([sys.executable, 'setup_seat_zones.py'], check=True)
            except:
                pass  # User might cancel, that's okay
        
        # Step 3: Start Server
        self.print_step(3, 3, "Starting detection server...")
        time.sleep(1)
        
        self.start_server()


def main():
    """Entry point"""
    try:
        launcher = SystemLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Launcher interrupted by user")
        print("👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()