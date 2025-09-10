const WebSocket = require('ws');

async function testWebSocketConnection() {
    console.log('🔌 Testing WebSocket connection to backend...');
    
    const wsUrl = 'ws://localhost:8000/ws/generation/test-session-123?token=test-auth-token';
    console.log('📡 Connecting to:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    
    ws.on('open', function open() {
        console.log('✅ WebSocket connection established!');
        
        // Send a test message
        const testMessage = {
            type: 'test_message',
            content: 'Hello from E2E test',
            timestamp: new Date().toISOString()
        };
        
        console.log('📤 Sending test message:', testMessage);
        ws.send(JSON.stringify(testMessage));
    });
    
    ws.on('message', function message(data) {
        try {
            const parsed = JSON.parse(data.toString());
            console.log('📥 Received message:', parsed);
        } catch (e) {
            console.log('📥 Received raw data:', data.toString());
        }
    });
    
    ws.on('error', function error(err) {
        console.log('❌ WebSocket error:', err.message);
    });
    
    ws.on('close', function close(code, reason) {
        console.log('🔌 WebSocket closed:', code, reason.toString());
    });
    
    // Keep connection open for a few seconds
    setTimeout(() => {
        console.log('⏰ Closing WebSocket connection...');
        ws.close();
    }, 5000);
}

testWebSocketConnection().catch(console.error);