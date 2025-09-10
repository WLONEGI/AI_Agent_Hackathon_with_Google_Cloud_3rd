/**
 * Frontend-Backend Integration Test
 * Tests the complete integration between frontend and backend services
 */

const { chromium } = require('playwright');

const FRONTEND_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';

class IntegrationTester {
  constructor() {
    this.browser = null;
    this.page = null;
  }

  async init() {
    console.log('🚀 Starting Frontend-Backend Integration Tests...\n');
    this.browser = await chromium.launch({ headless: false, slowMo: 1000 });
    this.page = await this.browser.newPage();
    
    // Listen for console errors
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      }
    });

    // Listen for network failures
    this.page.on('requestfailed', request => {
      console.log('🌐 Network Request Failed:', request.url(), request.failure().errorText);
    });
  }

  async testBackendHealth() {
    console.log('🔍 Testing Backend Health...');
    
    try {
      const response = await fetch(`${BACKEND_URL}/health`);
      const data = await response.json();
      
      if (data.status === 'healthy') {
        console.log('✅ Backend Health Check: PASSED');
        console.log(`   📊 Service: ${data.service}`);
        console.log(`   🎭 Mock Mode: ${data.mock_enabled}`);
        return true;
      } else {
        console.log('❌ Backend Health Check: FAILED');
        return false;
      }
    } catch (error) {
      console.log('❌ Backend Health Check: ERROR -', error.message);
      return false;
    }
  }

  async testMockAuth() {
    console.log('\n🔐 Testing Mock Authentication...');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com', password: 'testpassword' })
      });
      
      const data = await response.json();
      
      if (data.token && data.user) {
        console.log('✅ Mock Authentication: PASSED');
        console.log(`   👤 User: ${data.user.name} (${data.user.email})`);
        console.log(`   🔑 Token: ${data.token.substring(0, 20)}...`);
        return { success: true, token: data.token, user: data.user };
      } else {
        console.log('❌ Mock Authentication: FAILED');
        return { success: false };
      }
    } catch (error) {
      console.log('❌ Mock Authentication: ERROR -', error.message);
      return { success: false };
    }
  }

  async testMangaGeneration(authToken) {
    console.log('\n📚 Testing Manga Generation API...');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/manga/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          title: 'Integration Test Manga',
          text: 'A story about successful integration testing'
        })
      });
      
      const data = await response.json();
      
      if (data.session_id && data.status === 'processing') {
        console.log('✅ Manga Generation API: PASSED');
        console.log(`   📖 Session ID: ${data.session_id}`);
        console.log(`   📊 Status: ${data.status}`);
        console.log(`   📝 Title: ${data.title}`);
        console.log(`   👤 User ID: ${data.user_id}`);
        console.log(`   📋 Phases: ${data.phases.length} phases configured`);
        return { success: true, sessionId: data.session_id };
      } else {
        console.log('❌ Manga Generation API: FAILED');
        return { success: false };
      }
    } catch (error) {
      console.log('❌ Manga Generation API: ERROR -', error.message);
      return { success: false };
    }
  }

  async testWebSocketConnection(sessionId, authToken) {
    console.log('\n🔌 Testing WebSocket Connection...');
    
    return new Promise((resolve) => {
      try {
        const wsUrl = `ws://localhost:8000/ws/generation/${sessionId}?token=${encodeURIComponent(authToken)}`;
        console.log(`   🔗 Connecting to: ${wsUrl}`);
        
        const ws = new WebSocket(wsUrl);
        let connected = false;
        let messagesReceived = 0;
        
        ws.onopen = () => {
          connected = true;
          console.log('✅ WebSocket Connection: ESTABLISHED');
          
          // Send test message
          ws.send(JSON.stringify({
            type: 'test_message',
            data: { message: 'Integration test message' }
          }));
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            messagesReceived++;
            console.log(`   📨 Message ${messagesReceived}: ${data.type}`);
            
            if (data.type === 'connection_established') {
              console.log(`      ✅ Connection confirmed for session: ${data.session_id}`);
            } else if (data.type === 'message_received') {
              console.log(`      ✅ Echo received: ${data.response}`);
            }
            
            // Close after receiving a few messages
            if (messagesReceived >= 2) {
              ws.close();
              resolve({ 
                success: true, 
                connected, 
                messagesReceived 
              });
            }
          } catch (error) {
            console.log('❌ WebSocket Message Parse Error:', error.message);
          }
        };
        
        ws.onerror = (error) => {
          console.log('❌ WebSocket Error:', error.message || 'Connection failed');
          resolve({ success: false, connected, messagesReceived });
        };
        
        ws.onclose = () => {
          if (connected && messagesReceived >= 2) {
            console.log('✅ WebSocket Connection: CLOSED SUCCESSFULLY');
            resolve({ success: true, connected, messagesReceived });
          } else {
            console.log('❌ WebSocket Connection: CLOSED PREMATURELY');
            resolve({ success: false, connected, messagesReceived });
          }
        };
        
        // Timeout after 10 seconds
        setTimeout(() => {
          if (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
          resolve({ 
            success: connected && messagesReceived > 0, 
            connected, 
            messagesReceived,
            timeout: true 
          });
        }, 10000);
        
      } catch (error) {
        console.log('❌ WebSocket Test: ERROR -', error.message);
        resolve({ success: false, connected: false, messagesReceived: 0 });
      }
    });
  }

  async testFrontendLoad() {
    console.log('\n🖥️  Testing Frontend Load...');
    
    try {
      await this.page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
      
      // Wait for main content
      await this.page.waitForSelector('main', { timeout: 10000 });
      
      const title = await this.page.title();
      console.log(`✅ Frontend Load: PASSED`);
      console.log(`   📄 Page Title: ${title}`);
      
      // Check for any console errors
      const errors = [];
      this.page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      await this.page.waitForTimeout(2000);
      
      if (errors.length === 0) {
        console.log('   ✅ No console errors detected');
      } else {
        console.log(`   ⚠️  Console errors detected: ${errors.length}`);
        errors.forEach(error => console.log(`      - ${error}`));
      }
      
      return { success: true, title, errors };
    } catch (error) {
      console.log('❌ Frontend Load: ERROR -', error.message);
      return { success: false, error: error.message };
    }
  }

  async testFrontendBackendIntegration() {
    console.log('\n🔗 Testing Frontend-Backend Integration...');
    
    try {
      await this.page.goto(FRONTEND_URL);
      await this.page.waitForSelector('main');
      
      // Test API calls from frontend
      const apiHealthCheck = await this.page.evaluate(async () => {
        try {
          const response = await fetch('http://localhost:8000/health');
          const data = await response.json();
          return { success: true, data };
        } catch (error) {
          return { success: false, error: error.message };
        }
      });
      
      if (apiHealthCheck.success) {
        console.log('✅ Frontend → Backend API Call: PASSED');
        console.log(`   📊 Backend Status: ${apiHealthCheck.data.status}`);
      } else {
        console.log('❌ Frontend → Backend API Call: FAILED');
        console.log(`   ❌ Error: ${apiHealthCheck.error}`);
      }
      
      return apiHealthCheck;
    } catch (error) {
      console.log('❌ Frontend-Backend Integration: ERROR -', error.message);
      return { success: false };
    }
  }

  async runFullIntegrationTest() {
    console.log('🧪 Running Full Integration Test Suite...\n');
    
    const results = {
      backendHealth: false,
      mockAuth: false,
      mangaGeneration: false,
      webSocketConnection: false,
      frontendLoad: false,
      frontendBackendIntegration: false
    };
    
    // Test 1: Backend Health
    results.backendHealth = await this.testBackendHealth();
    
    // Test 2: Mock Authentication
    const authResult = await this.testMockAuth();
    results.mockAuth = authResult.success;
    
    if (authResult.success) {
      // Test 3: Manga Generation API
      const mangaResult = await this.testMangaGeneration(authResult.token);
      results.mangaGeneration = mangaResult.success;
      
      if (mangaResult.success) {
        // Test 4: WebSocket Connection
        const wsResult = await this.testWebSocketConnection(mangaResult.sessionId, authResult.token);
        results.webSocketConnection = wsResult.success;
      }
    }
    
    // Test 5: Frontend Load
    const frontendResult = await this.testFrontendLoad();
    results.frontendLoad = frontendResult.success;
    
    // Test 6: Frontend-Backend Integration
    const integrationResult = await this.testFrontendBackendIntegration();
    results.frontendBackendIntegration = integrationResult.success;
    
    return results;
  }

  async generateReport(results) {
    console.log('\n📊 INTEGRATION TEST REPORT');
    console.log('='.repeat(50));
    
    const tests = [
      { name: 'Backend Health Check', key: 'backendHealth' },
      { name: 'Mock Authentication', key: 'mockAuth' },
      { name: 'Manga Generation API', key: 'mangaGeneration' },
      { name: 'WebSocket Connection', key: 'webSocketConnection' },
      { name: 'Frontend Load', key: 'frontendLoad' },
      { name: 'Frontend-Backend Integration', key: 'frontendBackendIntegration' }
    ];
    
    let passed = 0;
    let total = tests.length;
    
    tests.forEach(test => {
      const status = results[test.key] ? '✅ PASSED' : '❌ FAILED';
      console.log(`${test.name}: ${status}`);
      if (results[test.key]) passed++;
    });
    
    console.log('\n📈 SUMMARY');
    console.log(`Passed: ${passed}/${total} (${Math.round(passed/total*100)}%)`);
    
    if (passed === total) {
      console.log('🎉 ALL TESTS PASSED! Frontend and Backend are properly integrated.');
    } else {
      console.log('⚠️  Some tests failed. Please review the integration setup.');
    }
    
    return { passed, total, success: passed === total };
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Run the integration test
(async () => {
  const tester = new IntegrationTester();
  
  try {
    await tester.init();
    const results = await tester.runFullIntegrationTest();
    const report = await tester.generateReport(results);
    
    process.exit(report.success ? 0 : 1);
  } catch (error) {
    console.error('❌ Integration Test Error:', error);
    process.exit(1);
  } finally {
    await tester.close();
  }
})();