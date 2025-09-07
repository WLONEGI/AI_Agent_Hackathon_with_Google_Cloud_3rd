// Jest performance setup
import '@testing-library/jest-dom';

// Environment
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000';

// Mock WebSocket
global.WebSocket = class MockWebSocket {
  constructor(url) { this.url = url; this.readyState = 1; }
  send() {}
  close() { this.readyState = 3; }
};

// Mock fetch
global.fetch = jest.fn();
