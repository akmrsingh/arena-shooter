// Multiplayer module using PeerJS for WebRTC connections
let peer = null;
let conn = null;
let isHost = false;
let roomCode = "";
let connectionStatus = "disconnected"; // disconnected, connecting, connected
let receivedData = [];
let onConnectCallback = null;

// Generate random 4-digit room code
function generateRoomCode() {
    return Math.floor(1000 + Math.random() * 9000).toString();
}

// Initialize PeerJS
function initPeer(id) {
    return new Promise((resolve, reject) => {
        peer = new Peer(id, {
            debug: 2
        });

        peer.on('open', (id) => {
            console.log('My peer ID is: ' + id);
            resolve(id);
        });

        peer.on('error', (err) => {
            console.error('Peer error:', err);
            connectionStatus = "disconnected";
            reject(err);
        });

        peer.on('connection', (connection) => {
            console.log('Incoming connection from:', connection.peer);
            conn = connection;
            setupConnection();
        });
    });
}

// Setup connection event handlers
function setupConnection() {
    conn.on('open', () => {
        console.log('Connection opened');
        connectionStatus = "connected";
        if (onConnectCallback) onConnectCallback();
    });

    conn.on('data', (data) => {
        receivedData.push(data);
    });

    conn.on('close', () => {
        console.log('Connection closed');
        connectionStatus = "disconnected";
        conn = null;
    });

    conn.on('error', (err) => {
        console.error('Connection error:', err);
        connectionStatus = "disconnected";
    });
}

// Host a game - create room and wait for player
async function hostGame() {
    roomCode = generateRoomCode();
    connectionStatus = "connecting";

    try {
        await initPeer("arena-" + roomCode);
        isHost = true;
        console.log('Hosting game with code:', roomCode);
        return roomCode;
    } catch (err) {
        connectionStatus = "disconnected";
        return null;
    }
}

// Join a game with room code
async function joinGame(code) {
    connectionStatus = "connecting";
    roomCode = code;

    try {
        await initPeer("arena-joiner-" + code + "-" + Date.now());
        isHost = false;

        // Connect to host
        conn = peer.connect("arena-" + code, {
            reliable: true
        });

        setupConnection();
        console.log('Joining game with code:', code);
        return true;
    } catch (err) {
        connectionStatus = "disconnected";
        return false;
    }
}

// Send data to peer
function sendData(data) {
    if (conn && conn.open) {
        conn.send(data);
        return true;
    }
    return false;
}

// Get received data (clears buffer)
function getReceivedData() {
    const data = [...receivedData];
    receivedData = [];
    return data;
}

// Get connection status
function getConnectionStatus() {
    return connectionStatus;
}

// Get room code
function getRoomCode() {
    return roomCode;
}

// Check if host
function getIsHost() {
    return isHost;
}

// Disconnect
function disconnect() {
    if (conn) {
        conn.close();
        conn = null;
    }
    if (peer) {
        peer.destroy();
        peer = null;
    }
    connectionStatus = "disconnected";
    roomCode = "";
    isHost = false;
}

// Expose to window for Python access
window.MP = {
    hostGame: hostGame,
    joinGame: joinGame,
    sendData: sendData,
    getReceivedData: getReceivedData,
    getConnectionStatus: getConnectionStatus,
    getRoomCode: getRoomCode,
    getIsHost: getIsHost,
    disconnect: disconnect
};

console.log("Multiplayer module loaded");
