// Infinite Backrooms - Client Application
// Complete frontend with system.css design

// State
let personas = [];
let messages = [];
let settings = {};
let isRunning = false;
let currentMessages = new Map(); // Track streaming messages

// Socket.IO connection
const socket = io();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initControls();
    initPersonaForm();
    initSettings();
    checkOllamaConnection();
});

// Socket event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    updateConnectionStatus(false);
});

socket.on('personas', (data) => {
    personas = data;
    renderPersonasList();
    renderActivePersonas();
    updateStats();
});

socket.on('messages', (data) => {
    messages = data;
    renderMessages();
    updateStats();
});

socket.on('settings', (data) => {
    settings = data;
    loadSettings();
});

socket.on('status', (data) => {
    isRunning = data.is_running;
    updateStatusUI();
});

socket.on('message_update', (message) => {
    currentMessages.set(message.id, message);
    renderMessages();
    scrollToBottom();
});

socket.on('message_final', (message) => {
    messages.push(message);
    currentMessages.delete(message.id);
    renderMessages();
    updateStats();
    scrollToBottom();
});

socket.on('error', (data) => {
    alert('Error: ' + data.message);
});

socket.on('info', (data) => {
    console.log('Info:', data.message);
});

// Tab management
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Controls
function initControls() {
    document.getElementById('start-btn').addEventListener('click', startConversation);
    document.getElementById('stop-btn').addEventListener('click', stopConversation);
    document.getElementById('next-btn').addEventListener('click', nextTurn);
    document.getElementById('clear-btn').addEventListener('click', clearMessages);
    document.getElementById('export-btn').addEventListener('click', exportData);
}

function startConversation() {
    socket.emit('start_conversation');
}

function stopConversation() {
    socket.emit('stop_conversation');
}

function nextTurn() {
    socket.emit('next_turn');
}

function clearMessages() {
    if (confirm('Clear all messages?')) {
        fetch('/api/messages', { method: 'DELETE' })
            .then(() => {
                messages = [];
                renderMessages();
                updateStats();
            });
    }
}

function exportData() {
    fetch('/api/export')
        .then(r => r.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `backroom-export-${new Date().toISOString()}.json`;
            a.click();
        });
}

// Render messages
function renderMessages() {
    const container = document.getElementById('messages-container');

    // Combine stored messages and streaming messages
    const allMessages = [...messages];

    // Add currently streaming messages
    currentMessages.forEach(msg => {
        if (!allMessages.find(m => m.id === msg.id)) {
            allMessages.push(msg);
        }
    });

    if (allMessages.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: #808080; padding: 20px;">
                <p><strong>No messages yet</strong></p>
                <p style="font-size: 8pt;">Click "Start" or "Next Turn" to begin</p>
            </div>
        `;
        return;
    }

    container.innerHTML = allMessages.map(msg => createMessageHTML(msg)).join('');
}

function createMessageHTML(message) {
    const content = highlightMentions(message.content);
    const thinkingVisible = message.thinking && message.thinking.trim() ? 'visible' : '';

    return `
        <div class="message" id="msg-${message.id}">
            <div class="message-header">
                <span class="persona-badge" style="background-color: ${message.persona_color};">
                    ${message.persona_role ? message.persona_role + ' ' : ''}${message.persona_name}
                </span>
                <span style="margin-left: 8px;">${message.timestamp}</span>
                ${message.streaming ? '<span style="margin-left: 8px;">●●●</span>' : ''}
            </div>
            <div class="message-content">${content || '<em>Generating...</em>'}</div>
            ${message.thinking ? `
                <div class="thinking ${thinkingVisible}">
                    <strong>🧠 Thinking:</strong><br>
                    ${escapeHtml(message.thinking)}
                </div>
            ` : ''}
        </div>
    `;
}

function highlightMentions(text) {
    if (!text) return '';

    let result = escapeHtml(text);

    personas.forEach(p => {
        const mention = `@${p.name}`;
        const regex = new RegExp(escapeRegex(mention), 'g');
        result = result.replace(regex, `<span class="mention">${mention}</span>`);
    });

    return result;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeRegex(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function scrollToBottom() {
    const container = document.getElementById('messages-container');
    container.scrollTop = container.scrollHeight;
}

// Persona management
function initPersonaForm() {
    document.getElementById('add-persona-btn').addEventListener('click', showPersonaForm);
    document.getElementById('save-persona-btn').addEventListener('click', savePersona);
    document.getElementById('cancel-persona-btn').addEventListener('click', hidePersonaForm);

    // Load roles
    fetch('/api/roles')
        .then(r => r.json())
        .then(roles => {
            const select = document.getElementById('persona-role');
            select.innerHTML = Object.keys(roles).map(role =>
                `<option value="${role}">${role || '(No role)'}</option>`
            ).join('');
        });

    // Load models
    fetch('/api/models')
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById('persona-model');
            if (data.models && data.models.length > 0) {
                select.innerHTML = data.models.map(model =>
                    `<option value="${model}">${model}</option>`
                ).join('');
            }
        });
}

function showPersonaForm(editPersona = null) {
    const form = document.getElementById('persona-form');
    form.style.display = 'block';

    if (editPersona) {
        document.getElementById('edit-persona-id').value = editPersona.id;
        document.getElementById('persona-name').value = editPersona.name;
        document.getElementById('persona-model').value = editPersona.model;
        document.getElementById('persona-role').value = editPersona.role;
        document.getElementById('persona-system-prompt').value = editPersona.system_prompt;
        document.getElementById('persona-color').value = editPersona.color;
        document.getElementById('persona-enabled').checked = editPersona.enabled;
    } else {
        document.getElementById('edit-persona-id').value = '';
        document.getElementById('persona-name').value = '';
        document.getElementById('persona-role').value = '';
        document.getElementById('persona-system-prompt').value = '';
        document.getElementById('persona-color').value = '#1f77b4';
        document.getElementById('persona-enabled').checked = true;
    }
}

function hidePersonaForm() {
    document.getElementById('persona-form').style.display = 'none';
}

function savePersona() {
    const id = document.getElementById('edit-persona-id').value;
    const data = {
        name: document.getElementById('persona-name').value,
        model: document.getElementById('persona-model').value,
        role: document.getElementById('persona-role').value,
        system_prompt: document.getElementById('persona-system-prompt').value,
        color: document.getElementById('persona-color').value,
        enabled: document.getElementById('persona-enabled').checked,
    };

    if (!data.name.trim()) {
        alert('Please enter a name');
        return;
    }

    const url = id ? `/api/personas/${id}` : '/api/personas';
    const method = id ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(() => {
            hidePersonaForm();
            loadPersonas();
        });
}

function loadPersonas() {
    fetch('/api/personas')
        .then(r => r.json())
        .then(data => {
            personas = data;
            renderPersonasList();
            renderActivePersonas();
            updateStats();
        });
}

function renderPersonasList() {
    const container = document.getElementById('personas-list');

    if (personas.length === 0) {
        container.innerHTML = '<p style="color: #808080;">No personas yet. Click "Add Persona" to create one.</p>';
        return;
    }

    container.innerHTML = personas.map(p => `
        <div class="persona-item">
            <div class="persona-info">
                <div>
                    <span class="persona-badge" style="background-color: ${p.color};">
                        ${p.name}
                    </span>
                    ${p.role ? `<span style="margin-left: 8px; font-size: 9px;">${p.role}</span>` : ''}
                </div>
                <div style="font-size: 8px; color: #808080; margin-top: 4px;">
                    ${p.model} ${p.enabled ? '✓ Enabled' : '✗ Disabled'}
                </div>
            </div>
            <div class="persona-actions">
                <button onclick="editPersona('${p.id}')">Edit</button>
                <button onclick="togglePersona('${p.id}')">${p.enabled ? 'Disable' : 'Enable'}</button>
                <button onclick="deletePersona('${p.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderActivePersonas() {
    const container = document.getElementById('active-personas-list');
    const active = personas.filter(p => p.enabled);

    if (active.length === 0) {
        container.innerHTML = '<p style="color: #808080;">No active personas</p>';
        return;
    }

    container.innerHTML = active.map(p => `
        <div style="margin-bottom: 4px;">
            <span class="persona-badge" style="background-color: ${p.color}; font-size: 8pt;">
                ${p.name}
            </span>
        </div>
    `).join('');
}

function editPersona(id) {
    const persona = personas.find(p => p.id === id);
    if (persona) {
        switchTab('personas');
        showPersonaForm(persona);
    }
}

function togglePersona(id) {
    const persona = personas.find(p => p.id === id);
    if (persona) {
        fetch(`/api/personas/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...persona, enabled: !persona.enabled }),
        })
            .then(() => loadPersonas());
    }
}

function deletePersona(id) {
    if (confirm('Delete this persona?')) {
        fetch(`/api/personas/${id}`, { method: 'DELETE' })
            .then(() => loadPersonas());
    }
}

// Settings
function initSettings() {
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);
    loadSettings();
}

function loadSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            settings = data;
            document.getElementById('setting-max-history').value = data.max_history;
            document.getElementById('setting-context-messages').value = data.context_messages;
            document.getElementById('setting-delay-min').value = data.response_delay_min;
            document.getElementById('setting-delay-max').value = data.response_delay_max;
            document.getElementById('setting-timeout').value = data.response_timeout;
            document.getElementById('setting-auto-advance').checked = data.auto_advance;
            document.getElementById('setting-enable-thinking').checked = data.enable_thinking;
        });
}

function saveSettings() {
    const data = {
        max_history: parseInt(document.getElementById('setting-max-history').value),
        context_messages: parseInt(document.getElementById('setting-context-messages').value),
        response_delay_min: parseFloat(document.getElementById('setting-delay-min').value),
        response_delay_max: parseFloat(document.getElementById('setting-delay-max').value),
        response_timeout: parseInt(document.getElementById('setting-timeout').value),
        auto_advance: document.getElementById('setting-auto-advance').checked,
        enable_thinking: document.getElementById('setting-enable-thinking').checked,
    };

    fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
        .then(() => {
            alert('Settings saved!');
            loadSettings();
        });
}

// UI updates
function updateStatusUI() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const statusBox = document.getElementById('status-box');
    const statusText = document.getElementById('status-text');
    const indicator = document.getElementById('status-indicator');

    if (isRunning) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusBox.classList.remove('stopped');
        statusBox.classList.add('running');
        statusText.textContent = 'Running';
        indicator.style.color = '#00ff00';
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusBox.classList.remove('running');
        statusBox.classList.add('stopped');
        statusText.textContent = 'Stopped';
        indicator.style.color = '#ff0000';
    }
}

function updateConnectionStatus(connected) {
    const status = document.getElementById('ollama-status');
    status.textContent = connected ? 'Connected' : 'Disconnected';
    status.style.color = connected ? '#008000' : '#ff0000';
}

function checkOllamaConnection() {
    fetch('/api/models')
        .then(r => r.json())
        .then(data => {
            updateConnectionStatus(data.connected);
        })
        .catch(() => {
            updateConnectionStatus(false);
        });
}

function updateStats() {
    document.getElementById('active-count').textContent = personas.filter(p => p.enabled).length;
    document.getElementById('message-count').textContent = messages.length;
    document.getElementById('total-messages').textContent = messages.length;
    document.getElementById('total-personas').textContent = personas.length;
}

// Initial load
setTimeout(() => {
    loadPersonas();
    loadSettings();
}, 100);
