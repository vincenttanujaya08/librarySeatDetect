import json
import random
from datetime import datetime, timedelta

# Konfigurasi
TOTAL_FRAMES = 100
CHANGE_EVERY_X_FRAMES = 5  # Data berubah setiap 5 frame
START_TIME = datetime.strptime("08:00:00", "%H:%M:%S")

# Daftar ID Kursi
seats = ["T1", "T2", "T3", "B1", "B2", "B3"]

# Variable penampung
data_output = []
current_status = {}

# Fungsi untuk mengacak status kursi (1=Occupied, 2=On-Hold, 3=Empty)
def generate_random_status():
    status = {}
    for seat in seats:
        # Bobot random: Lebih sering occupied/empty daripada on-hold
        status[seat] = random.choice([1, 1, 2, 3, 3]) 
    return status

# Generate data pertama kali
current_status = generate_random_status()

for i in range(TOTAL_FRAMES):
    # 1. Update Waktu (Setiap frame nambah 1 detik)
    current_time_obj = START_TIME + timedelta(seconds=i)
    time_str = current_time_obj.strftime("%H:%M:%S")
    
    # 2. Cek apakah saatnya ganti status (Kelipatan 5)
    # Jika i = 0, 5, 10, 15... maka generate status baru
    if i % CHANGE_EVERY_X_FRAMES == 0:
        current_status = generate_random_status()
        print(f"Frame {i+1}: Data Berubah -> {time_str}")
    else:
        # Jika bukan kelipatan 5, status TETAP SAMA dengan sebelumnya
        pass 

    # 3. Masukkan ke list
    entry = {
        "timestamp": time_str,
        "status_codes": current_status.copy() # Copy agar tidak mereferensi object yang sama
    }
    data_output.append(entry)

# Simpan ke file JSON
filename = 'Web/frontend/data/status_simulasi.json'
with open(filename, 'w') as f:
    json.dump(data_output, f, indent=2)

print(f"\nSukses! File '{filename}' berhasil dibuat dengan {TOTAL_FRAMES} data.")