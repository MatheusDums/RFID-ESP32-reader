// Configuration - Automatically detect backend host
const API_HOST = window.location.hostname ? `${window.location.hostname}:8000` : 'localhost:8000';
const API_BASE = `http://${API_HOST}`;
const WS_BASE = `ws://${API_HOST}/ws`;

// Global State
let lastScannedUID = "";
let registeredUsers = [];
let wsConnection = null;

// DOM Elements
const elApiStatus = document.getElementById('status-api');
const elApiVal = document.getElementById('val-api');
const elMqttStatus = document.getElementById('status-mqtt');
const elMqttVal = document.getElementById('val-mqtt');
const elWsStatus = document.getElementById('status-ws');
const elWsVal = document.getElementById('val-ws');

const elLastAccessContainer = document.getElementById('last-access-display');
const elLogsTbody = document.getElementById('logs-tbody');
const elUserForm = document.getElementById('user-form');
const elUserName = document.getElementById('user-name');
const elUserRfid = document.getElementById('user-rfid');
const elUserApartment = document.getElementById('user-apartment');
const elUserRole = document.getElementById('user-role');
const elUserActive = document.getElementById('user-active');
const elUsersListContainer = document.getElementById('users-list-container');
const elUserCount = document.getElementById('user-count');
const btnCaptureTag = document.getElementById('btn-capture-tag');
const btnClearLogs = document.getElementById('btn-clear-logs');

// Toast Notification Helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    
    // Automatically remove toast after animation ends
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Check Backend Health & Update Indicators
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            updateStatusIndicator(elApiStatus, elApiVal, 'ONLINE', 'pulse-green');
            // Mocking MQTT broker status check based on connection health
            updateStatusIndicator(elMqttStatus, elMqttVal, 'ATIVO', 'pulse-green');
        } else {
            throw new Error("API responded with an error");
        }
    } catch (e) {
        updateStatusIndicator(elApiStatus, elApiVal, 'OFFLINE', 'pulse-red');
        updateStatusIndicator(elMqttStatus, elMqttVal, 'INDISPONÍVEL', 'pulse-red');
    }
}

function updateStatusIndicator(containerEl, labelEl, value, pulseClass) {
    const dot = containerEl.querySelector('.status-dot');
    dot.className = `status-dot ${pulseClass}`;
    labelEl.textContent = value;
}

// WebSocket Connection Management
function connectWebSocket() {
    updateStatusIndicator(elWsStatus, elWsVal, 'Conectando...', 'pulse-orange');
    
    wsConnection = new WebSocket(WS_BASE);

    wsConnection.onopen = () => {
        updateStatusIndicator(elWsStatus, elWsVal, 'Conectado', 'pulse-green');
        showToast("Conexão em tempo real estabelecida!", "success");
    };

    wsConnection.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleLiveAccessEvent(data);
        } catch (err) {
            console.error("Error parsing WebSocket message:", err);
        }
    };

    wsConnection.onclose = () => {
        updateStatusIndicator(elWsStatus, elWsVal, 'Desconectado', 'pulse-red');
        showToast("Conexão WebSocket perdida. Tentando reconectar...", "error");
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };

    wsConnection.onerror = (err) => {
        console.error("WebSocket error:", err);
        wsConnection.close();
    };
}

// Handle incoming RFID events in real-time
function handleLiveAccessEvent(event) {
    // 1. Keep track of the tag UID
    lastScannedUID = event.uid;
    btnCaptureTag.classList.add('pulse-green');
    setTimeout(() => btnCaptureTag.classList.remove('pulse-green'), 1000);

    // 2. Format local date/time
    const scanTime = new Date(event.created_at);
    const timeStr = scanTime.toLocaleTimeString('pt-BR');
    
    // 3. Update Last Scan display Card
    const isAuthorized = event.status === 'authorized';
    const statusText = isAuthorized ? 'Acesso Liberado' : (event.reason === 'inactive' ? 'Acesso Negado (Inativo)' : 'Tag Não Cadastrada');
    const statusClass = isAuthorized ? 'scan-authorized' : 'scan-denied';
    const icon = isAuthorized ? 'fa-circle-check' : 'fa-circle-xmark';
    const apartmentText = event.apartment ? ` | ${event.apartment}` : '';
    const rssiText = event.rssi !== null ? `${event.rssi} dBm` : 'N/A';
    
    elLastAccessContainer.innerHTML = `
        <div class="scan-result-card ${statusClass}">
            <div class="scan-icon-container">
                <i class="fa-solid ${icon}"></i>
            </div>
            <div class="scan-details">
                <h3>${event.username}</h3>
                <p class="scan-status-info">${statusText}</p>
                <div class="scan-meta">
                    <span><i class="fa-solid fa-microchip"></i> UID: <strong>${event.uid}</strong></span>
                    <span><i class="fa-solid fa-clock"></i> Hora: ${timeStr}</span>
                    <span><i class="fa-solid fa-building"></i> Local: Portaria Principal</span>
                    <span><i class="fa-solid fa-signal"></i> Sinal: ${rssiText}</span>
                </div>
            </div>
        </div>
    `;

    // 4. Trigger audio feedback (synthesized notification beep)
    playNotificationBeep(isAuthorized);

    // 5. Toast alerts
    if (isAuthorized) {
        showToast(`Acesso autorizado para ${event.username}`, "success");
    } else {
        showToast(`Tentativa de acesso NEGADA: ${event.uid}`, "error");
    }

    // 6. Prepend scan log row in the history table
    addLogToTable(event, true);
}

// Beep simulation using Web Audio API
function playNotificationBeep(authorized) {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        if (authorized) {
            // Short high beep
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
            gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.15);
        } else {
            // Longer low buzz
            oscillator.type = 'sawtooth';
            oscillator.frequency.setValueAtTime(150, audioCtx.currentTime);
            gainNode.gain.setValueAtTime(0.15, audioCtx.currentTime);
            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.5);
        }
    } catch (e) {
        console.warn("Audio Context not supported or allowed yet:", e);
    }
}

// Add a log row in the Access History Table
function addLogToTable(log, prepend = false) {
    // Remove "no data" row if it exists
    const noData = elLogsTbody.querySelector('.no-data-row');
    if (noData) noData.remove();
    
    const scanTime = new Date(log.created_at);
    const dateStr = scanTime.toLocaleDateString('pt-BR');
    const timeStr = scanTime.toLocaleTimeString('pt-BR');
    
    const isAuthorized = log.status === 'authorized';
    const statusBadge = isAuthorized 
        ? '<span class="badge badge-authorized"><i class="fa-solid fa-check"></i> Liberado</span>' 
        : '<span class="badge badge-denied"><i class="fa-solid fa-xmark"></i> Negado</span>';
        
    const rssiText = log.rssi !== null ? `${log.rssi} dBm` : '-';
    
    // Find username by UID if not provided in the log object
    let username = log.username;
    if (!username) {
        const matchedUser = registeredUsers.find(u => u.rfid_uuid === log.uid);
        username = matchedUser ? matchedUser.name : 'Desconhecido';
    }

    const row = document.createElement('tr');
    row.innerHTML = `
        <td><span class="time-col" title="${dateStr}">${timeStr}</span></td>
        <td><strong>${username}</strong></td>
        <td><span class="uid-code">${log.uid}</span></td>
        <td>${statusBadge}</td>
        <td>${rssiText}</td>
    `;

    if (prepend) {
        elLogsTbody.insertBefore(row, elLogsTbody.firstChild);
        // Cap local log table rows at 50
        if (elLogsTbody.children.length > 50) {
            elLogsTbody.lastChild.remove();
        }
    } else {
        elLogsTbody.appendChild(row);
    }
}

// Fetch Initial Logs History
async function fetchLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs?limit=20`);
        if (response.ok) {
            const logs = await response.json();
            elLogsTbody.innerHTML = '';
            
            if (logs.length === 0) {
                elLogsTbody.innerHTML = `
                    <tr class="no-data-row">
                        <td colspan="5">Nenhuma leitura registrada recentemente.</td>
                    </tr>
                `;
                return;
            }
            
            logs.forEach(log => addLogToTable(log, false));
        }
    } catch (e) {
        console.error("Failed to fetch logs:", e);
    }
}

// Fetch Registered Users List
async function fetchUsers() {
    try {
        const response = await fetch(`${API_BASE}/users`);
        if (response.ok) {
            registeredUsers = await response.json();
            renderUsersList();
        }
    } catch (e) {
        console.error("Failed to fetch users:", e);
    }
}

// Render registered users in side-list
function renderUsersList() {
    elUsersListContainer.innerHTML = '';
    elUserCount.textContent = registeredUsers.length;

    if (registeredUsers.length === 0) {
        elUsersListContainer.innerHTML = `
            <div class="no-data-card">
                <i class="fa-regular fa-folder-open"></i>
                <p>Nenhum usuário cadastrado no banco SQLite.</p>
            </div>
        `;
        return;
    }

    registeredUsers.forEach(user => {
        const card = document.createElement('div');
        card.className = `user-item-card ${user.active ? '' : 'user-inactive'}`;
        
        // Get user initials for avatar
        const initials = user.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
        
        card.innerHTML = `
            <div class="user-info-main">
                <div class="user-avatar">${initials}</div>
                <div class="user-info-texts">
                    <h4>${user.name}</h4>
                    <p>
                        <span class="user-tag-badge">${user.rfid_uuid}</span>
                        ${user.apartment ? `<span>Apto: ${user.apartment}</span>` : ''}
                    </p>
                </div>
            </div>
            <div class="user-actions">
                <!-- Status Toggle -->
                <label class="toggle-switch user-toggle-active" title="Ativar/Desativar tag">
                    <input type="checkbox" ${user.active ? 'checked' : ''} onchange="toggleUserStatus(${user.id})">
                    <span class="slider"></span>
                </label>
                <!-- Delete Button -->
                <button class="btn-icon" onclick="deleteUser(${user.id})" title="Excluir Usuário">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `;
        elUsersListContainer.appendChild(card);
    });
}

// Toggle User Active Status (API Call)
async function toggleUserStatus(userId) {
    try {
        const response = await fetch(`${API_BASE}/users/${userId}/toggle-active`, {
            method: 'POST'
        });
        if (response.ok) {
            const data = await response.json();
            showToast(`Status de ${data.name} alterado para ${data.active ? 'Ativo' : 'Inativo'}!`, "success");
            fetchUsers(); // Refresh
        } else {
            showToast("Falha ao alterar status do usuário.", "error");
        }
    } catch (e) {
        console.error("Error toggling user status:", e);
        showToast("Erro de rede ao alterar status do usuário.", "error");
    }
}

// Delete User (API Call)
async function deleteUser(userId) {
    if (!confirm("Tem certeza que deseja excluir este usuário? O acesso desta tag será negado.")) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/users/${userId}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            showToast("Usuário excluído com sucesso!", "success");
            fetchUsers(); // Refresh
        } else {
            showToast("Falha ao excluir usuário.", "error");
        }
    } catch (e) {
        console.error("Error deleting user:", e);
        showToast("Erro de rede ao excluir usuário.", "error");
    }
}

// Form Submission - Create new User
elUserForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const payload = {
        name: elUserName.value,
        rfid_uuid: elUserRfid.value.trim().toUpperCase(),
        apartment: elUserApartment.value || null,
        role: elUserRole.value,
        active: elUserActive.checked
    };

    try {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showToast(`Usuário '${payload.name}' cadastrado com sucesso!`, "success");
            elUserForm.reset();
            elUserActive.checked = true; // reset toggle to default active
            fetchUsers(); // Refresh users list
        } else {
            const errData = await response.json();
            showToast(errData.detail || "Erro ao cadastrar usuário.", "error");
        }
    } catch (e) {
        console.error("Error registering user:", e);
        showToast("Erro de rede ao cadastrar usuário.", "error");
    }
});

// Capture Last Scanned Tag UID Button helper
btnCaptureTag.addEventListener('click', () => {
    if (lastScannedUID) {
        elUserRfid.value = lastScannedUID;
        showToast(`Tag ${lastScannedUID} copiada para o formulário!`, "success");
    } else {
        showToast("Nenhuma tag lida recentemente para capturar.", "error");
    }
});

// Clear table UI logs
btnClearLogs.addEventListener('click', () => {
    elLogsTbody.innerHTML = `
        <tr class="no-data-row">
            <td colspan="5">Nenhuma leitura registrada recentemente.</td>
        </tr>
    `;
    showToast("Histórico visual limpo.", "info");
});

// Initializations
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    fetchUsers().then(() => {
        fetchLogs();
    });
    connectWebSocket();
    
    // Poll API status every 10 seconds
    setInterval(checkHealth, 10000);
});
