// ===================== KONFIGURASI & STATUS =====================
const STATUS_MAP = {
  1: "Occupied", // Merah
  2: "On-Hold", // Kuning
  3: "Empty", // Hijau
};

// State global
let currentSelectedChair = null; // Element HTML kursi yang dipilih
let currentSelectedSeat = null; // Data object kursi yang dipilih
let currentSeats = []; // Menyimpan data status kursi saat ini
let lastTimestamp = "---";

// Log storage: Objek untuk menyimpan riwayat per kursi
// Format: { "T1": [ {t: "08:00:01", msg: "Empty -> Occupied"}, ... ], ... }
const currentSeatLogs = {};

// ===================== WEBSOCKET CONNECTION =====================
const socket = io("http://localhost:5000");

// Connection status handling
socket.on("connect", () => {
  console.log("✅ Connected to detection server!");
  updateConnectionStatus("Connected", true);

  // Auto-start detection saat connect
  console.log("🚀 Starting detection...");
  socket.emit("start_detection");
});

socket.on("disconnect", () => {
  console.log("❌ Disconnected from server");
  updateConnectionStatus("Disconnected", false);
});

socket.on("connection_status", (data) => {
  console.log("📡 Connection status:", data);
});

socket.on("detection_started", (data) => {
  console.log("✅ Detection started:", data);
  updateConnectionStatus("Detection Active", true);
});

socket.on("detection_stopped", (data) => {
  console.log("⏹️ Detection stopped:", data);
  updateConnectionStatus("Detection Stopped", false);
});

socket.on("error", (data) => {
  console.error("❌ Error from server:", data.message);
  alert("Error: " + data.message);
});

// REAL-TIME DATA UPDATES
socket.on("status_update", (data) => {
  // Process incoming data
  const { seatArray, timestamp } = processBackendData(data);

  // Check perubahan status untuk log
  seatArray.forEach((newSeat) => {
    const oldSeat = currentSeats.find((s) => s.id === newSeat.id);

    if (oldSeat && oldSeat.status !== newSeat.status) {
      // Hanya log jika status baru adalah Occupied
      if (newSeat.status === "Occupied") {
        addLogEntry(newSeat.id, timestamp, oldSeat.status, newSeat.status);
      }
    }
  });

  // Update global state
  currentSeats = seatArray;
  lastTimestamp = timestamp;

  // Update UI
  updateSummaryCards(currentSeats, lastTimestamp);
  renderSeatMap(currentSeats);
});

// Update connection status indicator
function updateConnectionStatus(message, isConnected) {
  const statusText = document.getElementById("last-updated-text");
  if (statusText) {
    const icon = isConnected ? "🟢" : "🔴";
    statusText.textContent = `${icon} ${message} | Last Updated: ${lastTimestamp}`;
  }
}

// ===================== LOGIC UTAMA (Helper & Render) =====================

// Mendapatkan class CSS berdasarkan status string
function getStatusClass(status) {
  switch (status) {
    case "Occupied":
      return "occupied-status";
    case "On-Hold":
      return "on-hold-status";
    case "Empty":
      return "empty-status";
    default:
      return "";
  }
}

// Render list log di Sidebar
function renderLogList(seatId) {
  const logList = document.getElementById("log-list");
  if (!logList) return;

  const logs = currentSeatLogs[seatId] || [];

  // Jika log kosong
  if (!logs.length) {
    logList.innerHTML =
      '<div class="log-placeholder">Belum ada perubahan status untuk kursi ini.</div>';
    return;
  }

  // Render HTML log (Maksimal 5 teratas)
  logList.innerHTML = logs
    .map((entry) => {
      return `
            <div class="log-entry">
                <span class="log-timestamp">${entry.t}</span>
                <span class="log-message">${entry.msg}</span>
            </div>
        `;
    })
    .join("");
}

// Handle saat kursi diklik
function handleSeatClick(seatId, chairElement) {
  // Cari data kursi terbaru dari array global
  const seatData = currentSeats.find((s) => s.id === seatId);
  currentSelectedSeat = seatData;

  // Visual effect (Highlight)
  if (currentSelectedChair) {
    currentSelectedChair.classList.remove("seat-selected", "seat-click-anim");
  }
  currentSelectedChair = chairElement;
  chairElement.classList.add("seat-selected");

  // Trigger animasi css restart
  chairElement.classList.remove("seat-click-anim");
  void chairElement.offsetWidth;
  chairElement.classList.add("seat-click-anim");

  // Update Sidebar
  showSeatDetails(seatId);
}

// Tampilkan detail di sidebar
function showSeatDetails(seatId) {
  const idSpan = document.getElementById("detail-id");
  if (idSpan) idSpan.textContent = seatId;
  renderLogList(seatId);
}

// Reset sidebar jika belum ada yang dipilih
function resetSeatDetails() {
  const idSpan = document.getElementById("detail-id");
  const logList = document.getElementById("log-list");
  if (idSpan) idSpan.textContent = "Klik salah satu kursi";
  if (logList)
    logList.innerHTML =
      '<div class="log-placeholder">Pilih kursi untuk melihat riwayat perubahan status.</div>';
}

// Parsing data JSON backend
function processBackendData(jsonObject) {
  const seatArray = [];
  const timestamp = jsonObject.timestamp;
  const statusCodes = jsonObject.status_codes;

  for (const seatId in statusCodes) {
    if (Object.prototype.hasOwnProperty.call(statusCodes, seatId)) {
      const statusCode = statusCodes[seatId];
      const statusString = STATUS_MAP[statusCode];
      if (statusString) {
        seatArray.push({
          id: seatId.toUpperCase(),
          status: statusString,
        });
      }
    }
  }
  return { seatArray, timestamp };
}

// Update Angka di Kartu Atas
function updateSummaryCards(data, timestamp) {
  const counts = { Occupied: 0, "On-Hold": 0, Empty: 0, Total: data.length };
  data.forEach((seat) => {
    if (Object.prototype.hasOwnProperty.call(counts, seat.status)) {
      counts[seat.status]++;
    }
  });

  document.getElementById("count-occupied").textContent = counts.Occupied;
  document.getElementById("count-on-hold").textContent = counts["On-Hold"];
  document.getElementById("count-empty").textContent = counts.Empty;
  document.getElementById(
    "last-updated-text"
  ).textContent = `Last Updated: ${timestamp}`;
  document.querySelector(
    ".logo h1"
  ).textContent = `📚 PETRA LIBRARY (Total: ${counts.Total})`;
}

// Render Warna Kursi di Peta
function renderSeatMap(data) {
  data.forEach((seat) => {
    // Cari elemen kursi di HTML berdasarkan atribut data-seat-id
    const chairElement = document.querySelector(
      `.chair[data-seat-id="${seat.id}"]`
    );
    if (chairElement) {
      // Update warna class
      const isSelected =
        currentSelectedChair === chairElement ? " seat-selected" : "";
      chairElement.className = `chair ${getStatusClass(
        seat.status
      )}${isSelected}`;

      // Pasang event listener click
      const seatWrapper = chairElement.closest(".seat-wrapper");
      if (seatWrapper) {
        seatWrapper.onclick = () => handleSeatClick(seat.id, chairElement);
      }
    }
  });
}

// Fungsi Mencatat Log (Maksimal 5)
function addLogEntry(seatId, timestamp, oldStatus, newStatus) {
  // Pesan log: "Empty -> Occupied"
  const message = `${oldStatus} ➝ ${newStatus}`;

  if (!currentSeatLogs[seatId]) {
    currentSeatLogs[seatId] = [];
  }

  // Tambah ke urutan paling atas
  currentSeatLogs[seatId].unshift({
    t: timestamp,
    msg: message,
  });

  // Potong jika lebih dari 5
  if (currentSeatLogs[seatId].length > 5) {
    currentSeatLogs[seatId] = currentSeatLogs[seatId].slice(0, 5);
  }

  // Jika user sedang melihat kursi ini, update sidebar realtime
  const idSpan = document.getElementById("detail-id");
  if (idSpan && idSpan.textContent === seatId) {
    renderLogList(seatId);
  }
}

// ===================== INISIALISASI PROGRAM =====================

document.addEventListener("DOMContentLoaded", () => {
  resetSeatDetails();
  console.log("🚀 Initializing Petra Library Seat Detection System...");
  console.log("📡 Connecting to WebSocket server...");

  // WebSocket will auto-connect and start detection
  // See socket.on('connect') handler above
});
