import json
from pathlib import Path

import cv2
import mss
import numpy as np


class SeatZoneSetupPrintOnly:
    def __init__(self):
        self.roi = None
        self.seat_zones = {}
        self.seat_ids = ["T1", "T2", "T3", "B1", "B2", "B3"]
        self.colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
        ]
        self.base_frame = None  # <- FRAME BEKU (1x screenshot)

    def load_roi(self) -> bool:
        roi_path = Path("config/monitor_roi.json")
        if not roi_path.exists():
            print("\n❌ ERROR: config/monitor_roi.json not found!")
            return False

        with roi_path.open("r", encoding="utf-8") as f:
            self.roi = json.load(f)

        needed = {"left", "top", "width", "height"}
        if not needed.issubset(set(self.roi.keys())):
            print("\n❌ ERROR: monitor_roi.json format salah (butuh left/top/width/height).")
            return False

        print(
            f"✅ Loaded ROI: {self.roi['width']}x{self.roi['height']} "
            f"at ({self.roi['left']}, {self.roi['top']})"
        )
        return True

    def capture_frame(self) -> np.ndarray:
        sct = mss.mss()
        img = np.array(sct.grab(self.roi))   # BGRA
        return img[:, :, :3].copy()          # BGR

    def draw_zones_on_frame(self, frame: np.ndarray, zones: dict) -> np.ndarray:
        vis = frame.copy()

        ordered = []
        for sid in [s.lower() for s in self.seat_ids]:
            if sid in zones:
                ordered.append((sid, zones[sid]))
        for k, v in zones.items():
            if k not in dict(ordered):
                ordered.append((k, v))

        for i, (seat_id, coords) in enumerate(ordered):
            x1, y1 = int(coords["x1"]), int(coords["y1"])
            x2, y2 = int(coords["x2"]), int(coords["y2"])
            color = self.colors[i % len(self.colors)]

            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 3)

            label = seat_id.upper()
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.9
            thickness = 2
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)

            y_top = max(0, y1 - th - 10)
            cv2.rectangle(vis, (x1, y_top), (x1 + tw + 10, y1), color, -1)
            cv2.putText(vis, label, (x1 + 5, y1 - 5),
                        font, font_scale, (255, 255, 255), thickness)

        return vis

    def freeze_base_frame(self):
        """Ambil 1x screenshot dan pakai itu terus untuk semua seat."""
        print("\n📸 Capturing ONE frozen frame (1x screenshot) ...")
        self.base_frame = self.capture_frame()

        # (Opsional) tampilkan sebentar supaya yakin frame-nya bener
        preview = self.base_frame.copy()
        cv2.putText(preview, "Frozen frame captured - Press any key",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow("Frozen Frame Preview", preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def setup_new_zones(self):
        print("\n" + "=" * 60)
        print("  INTERACTIVE SEAT ZONE SETUP (FROZEN FRAME)")
        print("=" * 60)
        print("\nFlow baru:")
        print("  1) Capture 1x screenshot (freeze)")
        print("  2) Kamu gambar T1..B3 di gambar yang sama")
        print("\n" + "=" * 60 + "\n")

        input("Press ENTER untuk mulai...")

        self.seat_zones = {}

        # ✅ Capture sekali saja
        self.freeze_base_frame()

        for idx, seat_id in enumerate(self.seat_ids, start=1):
            print(f"\n[{idx}/6] Setup seat: {seat_id}")

            # ✅ selalu pakai frame beku yang sama
            frame = self.base_frame.copy()

            # overlay zona yang sudah dibuat supaya jadi panduan
            if self.seat_zones:
                frame = self.draw_zones_on_frame(frame, self.seat_zones)

            instruction = f"Draw rectangle for {seat_id} - ENTER confirm | C redraw | ESC skip"
            cv2.putText(frame, instruction, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            roi = cv2.selectROI(f"Setup {seat_id}", frame, showCrosshair=True, fromCenter=False)
            cv2.destroyAllWindows()

            x, y, w, h = roi
            if w == 0 or h == 0:
                print(f"   ⚠️ Skipped {seat_id}")
                continue

            self.seat_zones[seat_id.lower()] = {
                "x1": int(x),
                "y1": int(y),
                "x2": int(x + w),
                "y2": int(y + h),
            }
            print(f"   ✅ {seat_id} defined: {w}x{h} at ({x}, {y})")

        print(f"\n✅ Setup selesai. Total zones: {len(self.seat_zones)}")

    def preview_final(self):
        if not self.seat_zones:
            print("❌ No zones defined, preview skipped.")
            return

        # ✅ pakai frame beku agar konsisten
        frame = self.base_frame.copy() if self.base_frame is not None else self.capture_frame()
        vis = self.draw_zones_on_frame(frame, self.seat_zones)

        cv2.putText(vis, "FINAL PREVIEW - Press any key to close",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("Final Seat Zones Preview", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def print_zones_json(self):
        print("\n" + "=" * 60)
        print("✅ COPY JSON INI KE: data/seat_zones.json")
        print("=" * 60)
        print(json.dumps(self.seat_zones, indent=2))
        print("=" * 60 + "\n")

    def run(self):
        print("\n" + "=" * 60)
        print("  PETRA LIBRARY - SEAT ZONE SETUP TOOL (FROZEN FRAME)")
        print("=" * 60 + "\n")

        if not self.load_roi():
            return

        self.setup_new_zones()
        self.preview_final()
        self.print_zones_json()

        print("Next:")
        print("1) Buat folder 'data/' kalau belum ada")
        print("2) Buat file 'data/seat_zones.json'")
        print("3) Paste JSON dari terminal ke file itu\n")


if __name__ == "__main__":
    SeatZoneSetupPrintOnly().run()
