'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { getWebSocketClient } from '@/lib/websocket';

interface APITestResult {
  endpoint: string;
  success: boolean;
  data?: any;
  error?: string;
  duration: number;
}

export function APITestButton() {
  const [isTesting, setIsTestnig] = useState(false);
  const [results, setResults] = useState<APITestResult[]>([]);

  const runAPITests = async () => {
    setIsTestnig(true);
    setResults([]);
    
    const testResults: APITestResult[] = [];

    // Test 1: Health Check
    const healthStart = Date.now();
    try {
      const healthResponse = await apiClient.healthCheck();
      testResults.push({
        endpoint: 'Health Check',
        success: healthResponse.success,
        data: healthResponse.data,
        error: healthResponse.error,
        duration: Date.now() - healthStart
      });
    } catch (error) {
      testResults.push({
        endpoint: 'Health Check',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - healthStart
      });
    }

    // Test 2: WebSocket Connection
    const wsStart = Date.now();
    try {
      const wsClient = getWebSocketClient();
      
      // WebSocket接続をテスト
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('WebSocket connection timeout')), 5000);
        
        wsClient.on('connected', (isConnected) => {
          clearTimeout(timeout);
          if (isConnected) {
            resolve(true);
          } else {
            reject(new Error('WebSocket connection failed'));
          }
        });
        
        wsClient.on('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
        
        wsClient.connect().catch(reject);
      });

      testResults.push({
        endpoint: 'WebSocket Connection',
        success: true,
        data: { connected: true, url: process.env.NEXT_PUBLIC_WS_URL },
        duration: Date.now() - wsStart
      });
      
      // WebSocket を切断
      getWebSocketClient().disconnect();
      
    } catch (error) {
      testResults.push({
        endpoint: 'WebSocket Connection',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - wsStart
      });
    }

    setResults(testResults);
    setIsTestnig(false);
  };

  return (
    <div className="space-y-4">
      <Button 
        onClick={runAPITests}
        disabled={isTestnig}
        variant="outline"
        className="w-full"
      >
        {isTestnig ? '接続テスト実行中...' : 'バックエンド接続テスト実行'}
      </Button>
      
      {results.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold text-sm">テスト結果:</h3>
          {results.map((result, index) => (
            <div 
              key={index} 
              className={`p-3 rounded-md text-xs ${
                result.success 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="font-medium">
                  {result.success ? '✅' : '❌'} {result.endpoint}
                </span>
                <span className="text-gray-500">
                  {result.duration}ms
                </span>
              </div>
              
              {result.success ? (
                <div className="text-green-700">
                  <strong>成功:</strong> 正常に接続されました
                  {result.data && (
                    <pre className="mt-1 text-xs overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  )}
                </div>
              ) : (
                <div className="text-red-700">
                  <strong>エラー:</strong> {result.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}