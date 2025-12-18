// ===================== KONFIGURASI & STATUS =====================
const STATUS_MAP = {
  1: "Occupied", // Merah
  2: "On-Hold", // Kuning
  3: "Empty", // Hijau
};

// State global
let currentSelectedChair = null;
let currentSelectedSeat = null;
let currentSeats = [];
let lastTimestamp = "---";

// Log storage: {seat_id: [{t, msg}, ...]}
const currentSeatLogs = {};

// ===================== WEBSOCKET CONNECTION =====================
const socket = io("http://localhost:5050");

socket.on("connect", () => {
  console.log("✅ Connected to detection server!");
  updateConnectionStatus("Connected", true);

  // Auto-start detection
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

  // Only show alert for actual errors, not "already running" messages
  if (!data.message.toLowerCase().includes("already running")) {
    alert("Error: " + data.message);
  } else {
    console.log("ℹ️ Detection already running, continuing...");
  }
});

// REAL-TIME DATA UPDATES
socket.on("status_update", (data) => {
  const { seatArray, timestamp } = processBackendData(data);

  // Check perubahan status untuk log
  seatArray.forEach((newSeat) => {
    const oldSeat = currentSeats.find((s) => s.id === newSeat.id);

    if (oldSeat && oldSeat.status !== newSeat.status) {
      // Log hanya kalau jadi Occupied
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

function updateConnectionStatus(message, isConnected) {
  const statusText = document.getElementById("last-updated-text");
  if (statusText) {
    const icon = isConnected ? "🟢" : "🔴";
    statusText.textContent = `${icon} ${message} | Last Updated: ${lastTimestamp}`;
  }
}

// ===================== LOGIC UTAMA =====================

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

function renderLogList(seatId) {
  const logList = document.getElementById("log-list");
  if (!logList) return;

  const logs = currentSeatLogs[seatId] || [];

  if (!logs.length) {
    logList.innerHTML =
      '<div class="log-placeholder">Belum ada perubahan status untuk kursi ini.</div>';
    return;
  }

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

function handleSeatClick(seatId, chairElement) {
  const seatData = currentSeats.find((s) => s.id === seatId);
  currentSelectedSeat = seatData;

  // Visual effect
  if (currentSelectedChair) {
    currentSelectedChair.classList.remove("seat-selected", "seat-click-anim");
  }
  currentSelectedChair = chairElement;
  chairElement.classList.add("seat-selected");

  // Trigger animasi
  chairElement.classList.remove("seat-click-anim");
  void chairElement.offsetWidth;
  chairElement.classList.add("seat-click-anim");

  // Update Sidebar
  showSeatDetails(seatId);
}

function showSeatDetails(seatId) {
  const idSpan = document.getElementById("detail-id");
  if (idSpan) idSpan.textContent = seatId;
  renderLogList(seatId);
}

function resetSeatDetails() {
  const idSpan = document.getElementById("detail-id");
  const logList = document.getElementById("log-list");
  if (idSpan) idSpan.textContent = "Klik salah satu kursi";
  if (logList)
    logList.innerHTML =
      '<div class="log-placeholder">Pilih kursi untuk melihat riwayat perubahan status.</div>';
}

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

function renderSeatMap(data) {
  data.forEach((seat) => {
    const chairElement = document.querySelector(
      `.chair[data-seat-id="${seat.id}"]`
    );
    if (chairElement) {
      const isSelected =
        currentSelectedChair === chairElement ? " seat-selected" : "";
      chairElement.className = `chair ${getStatusClass(
        seat.status
      )}${isSelected}`;

      const seatWrapper = chairElement.closest(".seat-wrapper");
      if (seatWrapper) {
        seatWrapper.onclick = () => handleSeatClick(seat.id, chairElement);
      }
    }
  });
}

function addLogEntry(seatId, timestamp, oldStatus, newStatus) {
  const message = `${oldStatus} ➝ ${newStatus}`;

  if (!currentSeatLogs[seatId]) {
    currentSeatLogs[seatId] = [];
  }

  currentSeatLogs[seatId].unshift({
    t: timestamp,
    msg: message,
  });

  // Max 5 logs
  if (currentSeatLogs[seatId].length > 5) {
    currentSeatLogs[seatId] = currentSeatLogs[seatId].slice(0, 5);
  }

  // Update sidebar jika user sedang lihat seat ini
  const idSpan = document.getElementById("detail-id");
  if (idSpan && idSpan.textContent === seatId) {
    renderLogList(seatId);
  }
}

// ===================== INISIALISASI =====================

document.addEventListener("DOMContentLoaded", () => {
  resetSeatDetails();
  console.log("🚀 Initializing Petra Library Seat Detection System...");
  console.log("📡 Connecting to WebSocket server...");
});
