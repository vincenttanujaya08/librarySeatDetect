// ===================== STATUS MAP ANGKA -> STRING =====================
const STATUS_MAP = {
    1: 'Occupied', // Merah
    2: 'On-Hold',  // Kuning (auto dari sistem)
    3: 'Empty'     // Hijau
};

// State global
let currentSelectedChair = null;
let currentSelectedSeat = null; // seat object yang lagi dipilih
let currentSeats = [];
let lastTimestamp = '---';
// Cup mode removed — manual reservation feature deleted
// Log storage per seat (id -> [{t: timestamp, msg: string}, ...])
const currentSeatLogs = {};


// ===================== HANDLE CLICK KURSI (hanya pilih kursi) =====================
function handleSeatClick(seat, chairElement) {
    currentSelectedSeat = seat;

    // Hapus highlight kursi sebelumnya
    if (currentSelectedChair) {
        currentSelectedChair.classList.remove('seat-selected', 'seat-click-anim');
    }

    // Set kursi ini sebagai terpilih
    currentSelectedChair = chairElement;
    chairElement.classList.add('seat-selected');

    // Trigger animasi klik (glow pendek)
    chairElement.classList.remove('seat-click-anim');
    void chairElement.offsetWidth; // force reflow supaya anim bisa diulang
    chairElement.classList.add('seat-click-anim');

    // Update panel detail & tombol
    showSeatDetails(seat);
}


// Manual Cup/Occupy actions removed


/**
 * Mengolah data JSON dari backend jadi array kursi.
 * @param {object} jsonObject JSON dari API.
 * @returns {{seatArray: Array, timestamp: string}}
 */
function processBackendData(jsonObject) {
    const seatArray = [];

    // Gunakan timestamp dari JSON untuk UI
    const timestamp = jsonObject.timestamp;

    // Status codes: { "T1": 1, "T2": 2, ... }
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


/**
 * Fetch data status kursi dari backend / file lokal.
 */
function fetchSeatStatusFromBackend() {
    const url = 'data/status_simulasi.json';

    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => processBackendData(data))
        .catch(error => {
            console.error('Error fetching data:', error);
            // Kalau gagal, balikin array kosong + timestamp sekarang
            return { seatArray: [], timestamp: new Date().toISOString() };
        });
}


// ===================== HELPER STATUS =====================

function getStatusClass(status) {
    switch (status) {
        case 'Occupied': return 'occupied-status';
        case 'On-Hold':  return 'on-hold-status';
        case 'Empty':    return 'empty-status'; 
        default:         return '';
    }
}

function getStatusMessage(status) {
    switch (status) {
        case 'Occupied':
            return 'Terpakai. Ada pengguna di kursi.';
        case 'On-Hold':
            return 'On-Hold. Ada barang tanpa orang (terdeteksi sistem).';
        case 'Empty':
            return 'Kosong. Siap digunakan oleh user.';
        default:
            return '---';
    }
}

function renderLogList(seatId) {
    const logList = document.getElementById('log-list');
    if (!logList) return;

    const logs = currentSeatLogs[seatId] || [];
    if (!logs.length) {
        logList.innerHTML = '<div class="log-placeholder">Tidak ada riwayat untuk kursi ini.</div>';
        return;
    }

    logList.innerHTML = logs.map(entry => {
        const ts = entry.t || '';
        const msg = entry.msg || '';
        return `<div class="log-entry"><span class="log-timestamp">${ts}</span><span class="log-message">${msg}</span></div>`;
    }).join('');
}


// ===================== RENDER MAP KURSI =====================

function renderSeatMap(data) {
    data.forEach(seat => {
        const chairElement = document.querySelector(`.chair[data-seat-id="${seat.id}"]`);
        if (chairElement) {
            // Set kelas warna berdasarkan status (merah/kuning/hijau)
            const extra = (currentSelectedChair === chairElement) ? ' seat-selected' : '';
            chairElement.className = `chair ${getStatusClass(seat.status)}${extra}`;

            const seatWrapper = chairElement.closest('.seat-wrapper');
            if (seatWrapper) {
                seatWrapper.onclick = () => handleSeatClick(seat, chairElement);
            }
        }
    });
}


// ===================== SUMMARY CARDS =====================

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

    // Update waktu dari backend
    document.getElementById('last-updated-text').textContent = `Last Updated: ${timestamp}`;
    document.querySelector('.logo h1').textContent = `📚 PETRA LIBRARY (Total: ${counts.Total})`;
}


// ===================== DETAIL KURSI (SIDEBAR) =====================

function showSeatDetails(seat) {
    const idSpan = document.getElementById('detail-id');
    idSpan.textContent = seat.id;
    renderLogList(seat.id);
}

function resetSeatDetails() {
    const idSpan = document.getElementById('detail-id');
    const logList = document.getElementById('log-list');
    idSpan.textContent = 'Klik salah satu kursi';
    if (logList) logList.innerHTML = '<div class="log-placeholder">Pilih kursi untuk melihat riwayat perubahan status.</div>';
}


// ===================== INITIALIZATION =====================

document.addEventListener('DOMContentLoaded', () => {
    resetSeatDetails();

    // Manual cup/occupy controls removed — UI is read-only with backend status

    // Data awal dari backend
    fetchSeatStatusFromBackend().then(({ seatArray, timestamp }) => {
        currentSeats = seatArray;
        lastTimestamp = timestamp;

        // Initialize logs for seats if needed
        seatArray.forEach(seat => {
            if (!currentSeatLogs[seat.id]) {
                currentSeatLogs[seat.id] = [];
            }
            if (currentSeatLogs[seat.id].length === 0) {
                currentSeatLogs[seat.id].push({ t: timestamp, msg: `Status set to ${seat.status}` });
            }
        });

        updateSummaryCards(currentSeats, lastTimestamp);
        renderSeatMap(currentSeats);
    });

    // Kalau mau polling backend:
    // setInterval(() => {
    //   fetchSeatStatusFromBackend().then(({ seatArray, timestamp }) => {
    //       currentSeats = seatArray;
    //       lastTimestamp = timestamp;
    //       updateSummaryCards(currentSeats, lastTimestamp);
    //       renderSeatMap(currentSeats);
    //   });
    // }, 5000);
});
