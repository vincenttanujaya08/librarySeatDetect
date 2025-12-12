import cv2
import mss
import numpy as np
import json

def setup_roi():
    """
    One-time setup untuk select area yang mau dimonitor
    Koordinat TIDAK langsung disimpan ke file, hanya di-print
    supaya bisa kamu copy-paste sendiri ke JSON.
    """
    print("="*60)
    print("  SETUP MONITOR AREA - PETRA LIBRARY SEAT DETECTION")
    print("="*60)
    print("\nInstruksi:")
    print("1. Screenshot full screen akan muncul")
    print("2. Drag mouse untuk select area perpustakaan yang mau dimonitor")
    print("3. Tekan ENTER untuk confirm")
    print("4. Tekan C untuk cancel dan ulang")
    print("\n" + "="*60 + "\n")
    
    sct = mss.mss()
    
    # Capture full screen
    full_monitor = sct.monitors[1]
    img_full = np.array(sct.grab(full_monitor))
    frame_full = img_full[:, :, :3]  # BGRA -> BGR
    
    print("📸 Screenshot captured. Please select the library area...")
    
    # Let user select ROI
    roi = cv2.selectROI(
        "Select Library Area to Monitor",
        frame_full,
        showCrosshair=True,
        fromCenter=False
    )
    cv2.destroyAllWindows()
    
    x, y, w, h = roi
    
    if w == 0 or h == 0:
        print("❌ No area selected. Exiting...")
        return None
    
    # Convert to absolute screen coordinates
    monitor_roi = {
        "left": int(full_monitor["left"] + x),
        "top": int(full_monitor["top"] + y),
        "width": int(w),
        "height": int(h)
    }
    
    print("\n✅ ROI captured!")
    print(f"   Area: {w}x{h} pixels")
    print(f"   Position: ({monitor_roi['left']}, {monitor_roi['top']})")
    
    # ==== BAGIAN BARU: hanya print JSON, tidak simpan file ====
    print("\n👉 Copy JSON berikut ke file config/monitor_roi.json:")
    print("=============================================")
    print(json.dumps(monitor_roi, indent=2))
    print("=============================================\n")
    
    # Show preview
    print("📺 Showing preview of selected area...")
    print("   Press any key to close preview")
    
    preview_img = np.array(sct.grab(monitor_roi))
    preview_frame = preview_img[:, :, :3]
    
    cv2.imshow('Selected Area Preview', preview_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n✅ Setup complete! Jangan lupa buat file config/monitor_roi.json dan paste JSON di atas.")
    
    return monitor_roi

if __name__ == "__main__":
    setup_roi()
