'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import {
  Gauge,
  Cpu,
  Zap,
  Monitor,
  Smartphone,
  Activity,
  Settings,
  AlertTriangle,
  CheckCircle,
  Info,
  WifiOff,
  Wifi
} from 'lucide-react';

export type QualityLevel = 1 | 2 | 3 | 4 | 5;

interface QualitySettings {
  level: QualityLevel;
  autoAdjust: boolean;
  imageQuality: 'low' | 'medium' | 'high' | 'ultra';
  animationEnabled: boolean;
  realtimePreview: boolean;
  aiProcessingPriority: 'speed' | 'balanced' | 'quality';
  maxConcurrentProcesses: number;
}

interface DevicePerformance {
  cpuUsage: number;
  memoryUsage: number;
  networkLatency: number;
  deviceType: 'mobile' | 'tablet' | 'desktop';
  browserCapabilities: {
    webgl: boolean;
    webworkers: boolean;
    offscreenCanvas: boolean;
  };
}

interface QualityAdjusterProps {
  onQualityChange: (settings: QualitySettings) => void;
  currentPhaseId?: number;
}

// 品質レベルごとの設定プリセット
const QUALITY_PRESETS: Record<QualityLevel, Partial<QualitySettings>> = {
  1: {
    imageQuality: 'low',
    animationEnabled: false,
    realtimePreview: false,
    aiProcessingPriority: 'speed',
    maxConcurrentProcesses: 1
  },
  2: {
    imageQuality: 'medium',
    animationEnabled: false,
    realtimePreview: false,
    aiProcessingPriority: 'speed',
    maxConcurrentProcesses: 2
  },
  3: {
    imageQuality: 'medium',
    animationEnabled: true,
    realtimePreview: false,
    aiProcessingPriority: 'balanced',
    maxConcurrentProcesses: 3
  },
  4: {
    imageQuality: 'high',
    animationEnabled: true,
    realtimePreview: true,
    aiProcessingPriority: 'balanced',
    maxConcurrentProcesses: 4
  },
  5: {
    imageQuality: 'ultra',
    animationEnabled: true,
    realtimePreview: true,
    aiProcessingPriority: 'quality',
    maxConcurrentProcesses: 5
  }
};

export function QualityAdjuster({ onQualityChange, currentPhaseId }: QualityAdjusterProps) {
  const [settings, setSettings] = useState<QualitySettings>({
    level: 3,
    autoAdjust: true,
    imageQuality: 'medium',
    animationEnabled: true,
    realtimePreview: false,
    aiProcessingPriority: 'balanced',
    maxConcurrentProcesses: 3
  });

  const [performance, setPerformance] = useState<DevicePerformance>({
    cpuUsage: 0,
    memoryUsage: 0,
    networkLatency: 0,
    deviceType: 'desktop',
    browserCapabilities: {
      webgl: false,
      webworkers: false,
      offscreenCanvas: false
    }
  });

  const [recommendedLevel, setRecommendedLevel] = useState<QualityLevel>(3);
  const [performanceWarning, setPerformanceWarning] = useState<string | null>(null);

  // デバイス性能を測定
  useEffect(() => {
    const measurePerformance = async () => {
      // デバイスタイプを判定
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      const isTablet = /iPad|Android/i.test(navigator.userAgent) && !isMobile;
      const deviceType = isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop';

      // ブラウザ機能を確認
      const webgl = !!document.createElement('canvas').getContext('webgl');
      const webworkers = typeof Worker !== 'undefined';
      const offscreenCanvas = typeof OffscreenCanvas !== 'undefined';

      // メモリ使用量を取得（可能な場合）
      let memoryUsage = 0;
      if ('memory' in performance && (performance as any).memory) {
        const memory = (performance as any).memory;
        memoryUsage = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
      }

      // CPU使用率の推定（簡易的）
      const start = performance.now();
      let iterations = 0;
      while (performance.now() - start < 100) {
        iterations++;
        Math.sqrt(iterations);
      }
      const cpuScore = iterations / 100000; // 正規化
      const cpuUsage = Math.max(0, Math.min(100, 100 - cpuScore * 10));

      // ネットワーク遅延の測定
      let networkLatency = 0;
      if ('connection' in navigator && (navigator as any).connection) {
        const connection = (navigator as any).connection;
        networkLatency = connection.rtt || 0;
      }

      setPerformance({
        cpuUsage,
        memoryUsage,
        networkLatency,
        deviceType,
        browserCapabilities: {
          webgl,
          webworkers,
          offscreenCanvas
        }
      });

      // 推奨品質レベルを計算
      let recommended: QualityLevel = 3;
      
      if (deviceType === 'mobile') {
        recommended = memoryUsage > 70 || cpuUsage > 80 ? 1 : 2;
      } else if (deviceType === 'tablet') {
        recommended = memoryUsage > 70 || cpuUsage > 80 ? 2 : 3;
      } else {
        if (memoryUsage < 30 && cpuUsage < 30 && webgl && webworkers) {
          recommended = 5;
        } else if (memoryUsage < 50 && cpuUsage < 50) {
          recommended = 4;
        } else if (memoryUsage < 70 && cpuUsage < 70) {
          recommended = 3;
        } else if (memoryUsage < 85 && cpuUsage < 85) {
          recommended = 2;
        } else {
          recommended = 1;
        }
      }

      setRecommendedLevel(recommended);

      // パフォーマンス警告を設定
      if (memoryUsage > 85 || cpuUsage > 85) {
        setPerformanceWarning('高負荷状態です。品質レベルを下げることを推奨します。');
      } else if (memoryUsage > 70 || cpuUsage > 70) {
        setPerformanceWarning('負荷が高めです。品質レベルの調整を検討してください。');
      } else {
        setPerformanceWarning(null);
      }
    };

    // 初回測定
    measurePerformance();

    // 定期的に測定（10秒ごと）
    const interval = setInterval(measurePerformance, 10000);

    return () => clearInterval(interval);
  }, []);

  // 自動調整が有効な場合、推奨レベルに合わせる
  useEffect(() => {
    if (settings.autoAdjust && recommendedLevel !== settings.level) {
      handleLevelChange(recommendedLevel);
    }
  }, [recommendedLevel, settings.autoAdjust]);

  // 品質レベルの変更
  const handleLevelChange = (level: QualityLevel) => {
    const preset = QUALITY_PRESETS[level];
    const newSettings = {
      ...settings,
      ...preset,
      level
    };
    setSettings(newSettings);
    onQualityChange(newSettings);
  };

  // 個別設定の変更
  const handleSettingChange = <K extends keyof QualitySettings>(
    key: K,
    value: QualitySettings[K]
  ) => {
    const newSettings = {
      ...settings,
      [key]: value
    };
    setSettings(newSettings);
    onQualityChange(newSettings);
  };

  // パフォーマンスインジケーターの色を取得
  const getPerformanceColor = (value: number) => {
    if (value < 30) return 'text-green-500';
    if (value < 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  // 品質レベルの説明を取得
  const getQualityDescription = (level: QualityLevel) => {
    const descriptions = {
      1: '最小負荷 - 低スペック端末向け',
      2: '低品質 - パフォーマンス優先',
      3: 'バランス - 標準的な品質',
      4: '高品質 - 高性能端末向け',
      5: '最高品質 - 最高のビジュアル体験'
    };
    return descriptions[level];
  };

  return (
    <Card className="bg-[rgb(var(--bg-secondary))] border-[rgb(var(--border-default))]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Gauge className="w-5 h-5 text-[rgb(var(--accent-primary))]" />
            <CardTitle className="text-base">品質設定</CardTitle>
          </div>
          <Badge variant={settings.autoAdjust ? "default" : "outline"} className="text-xs">
            {settings.autoAdjust ? '自動' : '手動'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* パフォーマンス警告 */}
        {performanceWarning && (
          <div className="flex items-center gap-2 p-2 rounded bg-yellow-500/10 border border-yellow-500/20">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            <span className="text-xs text-yellow-500">{performanceWarning}</span>
          </div>
        )}

        {/* 品質レベルスライダー */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm text-[rgb(var(--text-secondary))]">
              品質レベル
            </label>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                Level {settings.level}
              </Badge>
              {settings.level === recommendedLevel && (
                <Badge variant="outline" className="text-xs text-green-500 border-green-500">
                  推奨
                </Badge>
              )}
            </div>
          </div>
          <Slider
            value={[settings.level]}
            onValueChange={([value]) => handleLevelChange(value as QualityLevel)}
            min={1}
            max={5}
            step={1}
            className="w-full"
          />
          <p className="text-xs text-[rgb(var(--text-tertiary))]">
            {getQualityDescription(settings.level)}
          </p>
        </div>

        {/* 自動調整トグル */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-[rgb(var(--text-tertiary))]" />
            <label className="text-sm text-[rgb(var(--text-secondary))]">
              自動品質調整
            </label>
          </div>
          <Switch
            checked={settings.autoAdjust}
            onCheckedChange={(checked) => handleSettingChange('autoAdjust', checked)}
          />
        </div>

        {/* パフォーマンスメトリクス */}
        <div className="space-y-2 pt-2 border-t border-[rgb(var(--border-default))]">
          <h4 className="text-xs font-medium text-[rgb(var(--text-secondary))]">
            システム状態
          </h4>
          
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center gap-2">
              <Cpu className={`w-3 h-3 ${getPerformanceColor(performance.cpuUsage)}`} />
              <span className="text-xs text-[rgb(var(--text-tertiary))]">
                CPU: {Math.round(performance.cpuUsage)}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Activity className={`w-3 h-3 ${getPerformanceColor(performance.memoryUsage)}`} />
              <span className="text-xs text-[rgb(var(--text-tertiary))]">
                メモリ: {Math.round(performance.memoryUsage)}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              {performance.networkLatency < 100 ? (
                <Wifi className="w-3 h-3 text-green-500" />
              ) : (
                <WifiOff className="w-3 h-3 text-red-500" />
              )}
              <span className="text-xs text-[rgb(var(--text-tertiary))]">
                遅延: {performance.networkLatency}ms
              </span>
            </div>
            <div className="flex items-center gap-2">
              {performance.deviceType === 'mobile' ? (
                <Smartphone className="w-3 h-3 text-[rgb(var(--text-tertiary))]" />
              ) : (
                <Monitor className="w-3 h-3 text-[rgb(var(--text-tertiary))]" />
              )}
              <span className="text-xs text-[rgb(var(--text-tertiary))]">
                {performance.deviceType}
              </span>
            </div>
          </div>
        </div>

        {/* 詳細設定（手動モード時のみ） */}
        {!settings.autoAdjust && (
          <div className="space-y-3 pt-2 border-t border-[rgb(var(--border-default))]">
            <h4 className="text-xs font-medium text-[rgb(var(--text-secondary))]">
              詳細設定
            </h4>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs text-[rgb(var(--text-tertiary))]">
                  画像品質
                </label>
                <select
                  value={settings.imageQuality}
                  onChange={(e) => handleSettingChange('imageQuality', e.target.value as any)}
                  className="px-2 py-1 text-xs bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded"
                >
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                  <option value="ultra">最高</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <label className="text-xs text-[rgb(var(--text-tertiary))]">
                  アニメーション
                </label>
                <Switch
                  checked={settings.animationEnabled}
                  onCheckedChange={(checked) => handleSettingChange('animationEnabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="text-xs text-[rgb(var(--text-tertiary))]">
                  リアルタイムプレビュー
                </label>
                <Switch
                  checked={settings.realtimePreview}
                  onCheckedChange={(checked) => handleSettingChange('realtimePreview', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="text-xs text-[rgb(var(--text-tertiary))]">
                  AI処理優先度
                </label>
                <select
                  value={settings.aiProcessingPriority}
                  onChange={(e) => handleSettingChange('aiProcessingPriority', e.target.value as any)}
                  className="px-2 py-1 text-xs bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded"
                >
                  <option value="speed">速度優先</option>
                  <option value="balanced">バランス</option>
                  <option value="quality">品質優先</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <label className="text-xs text-[rgb(var(--text-tertiary))]">
                  並行処理数
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={settings.maxConcurrentProcesses}
                  onChange={(e) => handleSettingChange('maxConcurrentProcesses', parseInt(e.target.value))}
                  className="w-12 px-2 py-1 text-xs bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded text-center"
                />
              </div>
            </div>
          </div>
        )}

        {/* ブラウザ機能サポート状況 */}
        <div className="space-y-1 pt-2 border-t border-[rgb(var(--border-default))]">
          <h4 className="text-xs font-medium text-[rgb(var(--text-secondary))] mb-2">
            ブラウザ機能
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(performance.browserCapabilities).map(([key, supported]) => (
              <div key={key} className="flex items-center gap-1">
                {supported ? (
                  <CheckCircle className="w-3 h-3 text-green-500" />
                ) : (
                  <AlertTriangle className="w-3 h-3 text-yellow-500" />
                )}
                <span className="text-xs text-[rgb(var(--text-tertiary))]">
                  {key}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 現在のフェーズ情報 */}
        {currentPhaseId && (
          <div className="flex items-center gap-2 pt-2 border-t border-[rgb(var(--border-default))]">
            <Info className="w-3 h-3 text-[rgb(var(--text-tertiary))]" />
            <span className="text-xs text-[rgb(var(--text-tertiary))]">
              フェーズ {currentPhaseId} 処理中
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}