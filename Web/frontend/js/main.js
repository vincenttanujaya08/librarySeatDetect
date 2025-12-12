// ===================== KONFIGURASI & STATUS =====================
const STATUS_MAP = {
    1: 'Occupied', // Merah
    2: 'On-Hold',  // Kuning
    3: 'Empty'     // Hijau
};

// State global
let currentSelectedChair = null; // Element HTML kursi yang dipilih
let currentSelectedSeat = null;  // Data object kursi yang dipilih
let currentSeats = [];           // Menyimpan data status kursi saat ini
let lastTimestamp = '---';

// Log storage: Objek untuk menyimpan riwayat per kursi
// Format: { "T1": [ {t: "08:00:01", msg: "Empty -> Occupied"}, ... ], ... }
const currentSeatLogs = {};


// ===================== LOGIC UTAMA (Helper & Render) =====================

// Mendapatkan class CSS berdasarkan status string
function getStatusClass(status) {
    switch (status) {
        case 'Occupied': return 'occupied-status';
        case 'On-Hold':  return 'on-hold-status';
        case 'Empty':    return 'empty-status'; 
        default:         return '';
    }
}

// Render list log di Sidebar
function renderLogList(seatId) {
    const logList = document.getElementById('log-list');
    if (!logList) return;

    const logs = currentSeatLogs[seatId] || [];
    
    // Jika log kosong
    if (!logs.length) {
        logList.innerHTML = '<div class="log-placeholder">Belum ada perubahan status untuk kursi ini.</div>';
        return;
    }

    // Render HTML log (Maksimal 5 teratas)
    logList.innerHTML = logs.map(entry => {
        return `
            <div class="log-entry">
                <span class="log-timestamp">${entry.t}</span>
                <span class="log-message">${entry.msg}</span>
            </div>
        `;
    }).join('');
}

// Handle saat kursi diklik
function handleSeatClick(seatId, chairElement) {
    // Cari data kursi terbaru dari array global
    const seatData = currentSeats.find(s => s.id === seatId);
    currentSelectedSeat = seatData;

    // Visual effect (Highlight)
    if (currentSelectedChair) {
        currentSelectedChair.classList.remove('seat-selected', 'seat-click-anim');
    }
    currentSelectedChair = chairElement;
    chairElement.classList.add('seat-selected');
    
    // Trigger animasi css restart
    chairElement.classList.remove('seat-click-anim');
    void chairElement.offsetWidth; 
    chairElement.classList.add('seat-click-anim');

    // Update Sidebar
    showSeatDetails(seatId);
}

// Tampilkan detail di sidebar
function showSeatDetails(seatId) {
    const idSpan = document.getElementById('detail-id');
    if(idSpan) idSpan.textContent = seatId;
    renderLogList(seatId);
}

// Reset sidebar jika belum ada yang dipilih
function resetSeatDetails() {
    const idSpan = document.getElementById('detail-id');
    const logList = document.getElementById('log-list');
    if(idSpan) idSpan.textContent = 'Klik salah satu kursi';
    if(logList) logList.innerHTML = '<div class="log-placeholder">Pilih kursi untuk melihat riwayat perubahan status.</div>';
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
                    status: statusString
                });
            }
        }
    }
    return { seatArray, timestamp };
}

// Update Angka di Kartu Atas
function updateSummaryCards(data, timestamp) {
    const counts = { Occupied: 0, 'On-Hold': 0, Empty: 0, Total: data.length };
    data.forEach(seat => {
        if (Object.prototype.hasOwnProperty.call(counts, seat.status)) {
            counts[seat.status]++;
        }
    });

    document.getElementById('count-occupied').textContent = counts.Occupied;
    document.getElementById('count-on-hold').textContent = counts['On-Hold'];
    document.getElementById('count-empty').textContent = counts.Empty;
    document.getElementById('last-updated-text').textContent = `Last Updated: ${timestamp}`;
    document.querySelector('.logo h1').textContent = `📚 PETRA LIBRARY (Total: ${counts.Total})`;
}

// Render Warna Kursi di Peta
function renderSeatMap(data) {
    data.forEach(seat => {
        // Cari elemen kursi di HTML berdasarkan atribut data-seat-id
        const chairElement = document.querySelector(`.chair[data-seat-id="${seat.id}"]`);
        if (chairElement) {
            // Update warna class
            const isSelected = (currentSelectedChair === chairElement) ? ' seat-selected' : '';
            chairElement.className = `chair ${getStatusClass(seat.status)}${isSelected}`;

            // Pasang event listener click
            const seatWrapper = chairElement.closest('.seat-wrapper');
            if (seatWrapper) {
                seatWrapper.onclick = () => handleSeatClick(seat.id, chairElement);
            }
        }
    });
}


// ===================== LOGIC SIMULASI & HISTORY =====================

let simulationData = [];    
let currentIndex = 0;       
let simulationInterval = null;

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
        msg: message
    });

    // Potong jika lebih dari 5
    if (currentSeatLogs[seatId].length > 5) {
        currentSeatLogs[seatId] = currentSeatLogs[seatId].slice(0, 5);
    }

    // Jika user sedang melihat kursi ini, update sidebar realtime
    const idSpan = document.getElementById('detail-id');
    if (idSpan && idSpan.textContent === seatId) {
        renderLogList(seatId);
    }
}

// Langkah Update Per Detik
// ===================== LOGIC UPDATE PER DETIK =====================

function runUpdateStep() {
    // 1. Ambil data frame simulasi saat ini
    const currentFrame = simulationData[currentIndex];
    
    // 2. Olah data
    const processed = processBackendData(currentFrame);
    const newSeatArray = processed.seatArray;
    const newTimestamp = processed.timestamp;

    // 3. CEK PERUBAHAN STATUS & UPDATE LOG
    newSeatArray.forEach(newSeat => {
        // Cari status lama kursi ini di array global
        const oldSeat = currentSeats.find(s => s.id === newSeat.id);

        if (oldSeat) {
            // Jika status berubah
            if (oldSeat.status !== newSeat.status) {
                
                // --- FILTER LOGIKA BARU ---
                // Hanya catat log jika status BARU adalah 'Occupied' (Merah)
                if (newSeat.status === 'Occupied') {
                    addLogEntry(newSeat.id, newTimestamp, oldSeat.status, newSeat.status);
                }
                
            }
        }
    });

    // 4. Update Global State
    currentSeats = newSeatArray;
    lastTimestamp = newTimestamp;

    // 5. Update Tampilan
    updateSummaryCards(currentSeats, lastTimestamp);
    renderSeatMap(currentSeats);

    // 6. Maju ke frame berikutnya
    currentIndex++; 
    
    // 7. Looping jika data habis
    if (currentIndex >= simulationData.length) {
        currentIndex = 0; 
    }
}

function startSimulationLoop() {
    if (!simulationData || simulationData.length === 0) return;

    // Load frame pertama (tanpa log karena belum ada perbandingan)
    const firstFrame = simulationData[0];
    const { seatArray, timestamp } = processBackendData(firstFrame);
    
    currentSeats = seatArray; 
    lastTimestamp = timestamp;
    
    updateSummaryCards(currentSeats, lastTimestamp);
    renderSeatMap(currentSeats);

    // Mulai loop dari index 1
    currentIndex = 1;

    // Jalankan interval 1 detik (1000ms)
    simulationInterval = setInterval(() => {
        runUpdateStep();
    }, 1000); 
}


// ===================== INISIALISASI PROGRAM =====================

document.addEventListener('DOMContentLoaded', () => {
    resetSeatDetails();

    // Fetch File JSON
    fetch('data/status_simulasi.json')
        .then(response => {
            if (!response.ok) throw new Error("Gagal load JSON");
            return response.json();
        })
        .then(data => {
            if (Array.isArray(data)) {
                // Mode Simulasi (Array)
                simulationData = data;
                console.log(`Berhasil memuat ${data.length} frame simulasi.`);
                startSimulationLoop();
            } else {
                // Mode Static (Object tunggal) - Fallback
                const { seatArray, timestamp } = processBackendData(data);
                currentSeats = seatArray;
                updateSummaryCards(seatArray, timestamp);
                renderSeatMap(seatArray);
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('last-updated-text').textContent = "Error loading data.";
        });
});