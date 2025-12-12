from ultralytics import YOLO
import cv2
import numpy as np
import mss

def main():
    model = YOLO("yolov8s.pt")  # atau model kamu sendiri
    sct = mss.mss()

    # Ambil monitor utama (full screen)
    full_monitor = sct.monitors[1]

    # Screenshot full screen sekali
    img_full = np.array(sct.grab(full_monitor))
    frame_full = img_full[:, :, :3]  # BGRA -> BGR

    # === INI BAGIAN “PYTHON TAU PHOT0 BOOTH DI MANA” ===
    print("Silakan blok area jendela Photo Booth, lalu tekan ENTER.")
    roi = cv2.selectROI("Pilih area Photo Booth", frame_full,
                        showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Pilih area Photo Booth")
    # roi = (x, y, w, h) relatif terhadap full_monitor

    x, y, w, h = roi
    if w == 0 or h == 0:
        print("Area tidak dipilih, keluar.")
        return

    # Ubah ke koordinat absolut di layar
    monitor_roi = {
        "left": full_monitor["left"] + x,
        "top": full_monitor["top"] + y,
        "width": w,
        "height": h
    }

    print("Mulai deteksi YOLO. Tekan 'q' untuk keluar.")

    while True:
        
        # Capture hanya area Photo Booth
        img = np.array(sct.grab(monitor_roi))
        frame = img[:, :, :3]
        print(frame.shape)
        results = model(frame, conf=0.5)
        annotated = results[0].plot()

        cv2.imshow("YOLO dari Photo Booth (iPhone cam)", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
