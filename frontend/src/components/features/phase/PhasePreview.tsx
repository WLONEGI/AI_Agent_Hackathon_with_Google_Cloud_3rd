'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { type PhaseId } from '@/types/processing';

interface PhasePreviewProps {
  phaseId: PhaseId;
  data: any;
  isActive?: boolean;
  onFeedback?: (feedback: string) => void;
}

export function PhasePreview({ phaseId, data, isActive, onFeedback }: PhasePreviewProps) {
  const renderPhaseContent = () => {
    switch (phaseId) {
      case 1:
        return <Phase1ConceptPreview data={data} />;
      case 2:
        return <Phase2CharacterPreview data={data} />;
      case 3:
        return <Phase3PlotPreview data={data} />;
      case 4:
        return <Phase4NamePreview data={data} />;
      case 5:
        return <Phase5ImagePreview data={data} />;
      case 6:
        return <Phase6DialoguePreview data={data} />;
      case 7:
        return <Phase7IntegrationPreview data={data} />;
      default:
        return null;
    }
  };

  return (
    <div className={`transition-all duration-300 ${isActive ? 'scale-105' : ''}`}>
      {renderPhaseContent()}
    </div>
  );
}

// Phase 1: コンセプト・世界観分析
function Phase1ConceptPreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">コンセプト・世界観</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">テーマ</h4>
          <p className="text-[rgb(var(--text-primary))]">{data?.theme || '分析中...'}</p>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">ジャンル</h4>
          <div className="flex gap-2">
            {data?.genres?.map((genre: string, index: number) => (
              <Badge key={index} variant="secondary">{genre}</Badge>
            )) || <Badge variant="outline">未設定</Badge>}
          </div>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">世界観</h4>
          <p className="text-sm text-[rgb(var(--text-tertiary))]">{data?.worldSetting || '構築中...'}</p>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">対象読者層</h4>
          <p className="text-sm text-[rgb(var(--text-tertiary))]">{data?.targetAudience || '設定中...'}</p>
        </div>
      </CardContent>
    </Card>
  );
}

// Phase 2: キャラクター設定
function Phase2CharacterPreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">キャラクター設定</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data?.characters?.map((char: any, index: number) => (
          <div key={index} className="p-3 bg-[rgb(var(--bg-primary))] rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold">{char.name || `キャラクター${index + 1}`}</h4>
              <Badge variant="outline">{char.role || '役割'}</Badge>
            </div>
            <p className="text-sm text-[rgb(var(--text-secondary))] mb-2">{char.description}</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[rgb(var(--text-tertiary))]">年齢: </span>
                <span>{char.age || '不明'}</span>
              </div>
              <div>
                <span className="text-[rgb(var(--text-tertiary))]">性格: </span>
                <span>{char.personality || '設定中'}</span>
              </div>
            </div>
          </div>
        )) || <p className="text-[rgb(var(--text-tertiary))]">キャラクター生成中...</p>}
      </CardContent>
    </Card>
  );
}

// Phase 3: プロット・ストーリー構成
function Phase3PlotPreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">プロット構成</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">第1幕: 設定</h4>
          <p className="text-sm text-[rgb(var(--text-primary))]">{data?.act1 || '構成中...'}</p>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">第2幕: 対立</h4>
          <p className="text-sm text-[rgb(var(--text-primary))]">{data?.act2 || '構成中...'}</p>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">第3幕: 解決</h4>
          <p className="text-sm text-[rgb(var(--text-primary))]">{data?.act3 || '構成中...'}</p>
        </div>
        <div className="pt-2 border-t border-[rgb(var(--border-default))]">
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">キーポイント</h4>
          <ul className="list-disc list-inside text-sm text-[rgb(var(--text-tertiary))]">
            {data?.keyPoints?.map((point: string, index: number) => (
              <li key={index}>{point}</li>
            )) || <li>ポイント生成中...</li>}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

// Phase 4: ネーム生成
function Phase4NamePreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">ネーム（コマ割り）</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {data?.pages?.map((page: any, pageIndex: number) => (
            <div key={pageIndex} className="bg-[rgb(var(--bg-primary))] rounded-lg p-3">
              <h5 className="text-sm font-semibold mb-2">ページ {pageIndex + 1}</h5>
              <div className="space-y-2">
                {page.panels?.map((panel: any, panelIndex: number) => (
                  <div key={panelIndex} className="text-xs p-2 bg-[rgb(var(--bg-secondary))] rounded">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">コマ {panelIndex + 1}</span>
                      <Badge variant="outline" className="text-xs">{panel.size || '中'}</Badge>
                    </div>
                    <p className="text-[rgb(var(--text-tertiary))]">{panel.description}</p>
                    {panel.dialogue && (
                      <p className="mt-1 italic text-[rgb(var(--text-secondary))]">「{panel.dialogue}」</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )) || <p className="text-[rgb(var(--text-tertiary))]">ネーム生成中...</p>}
        </div>
      </CardContent>
    </Card>
  );
}

// Phase 5: シーン画像生成
function Phase5ImagePreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">画像生成プレビュー</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {data?.images?.map((image: any, index: number) => (
            <div key={index} className="space-y-2">
              <div className="aspect-square bg-[rgb(var(--bg-primary))] rounded-lg flex items-center justify-center">
                {image.url ? (
                  <img src={image.url} alt={`Scene ${index + 1}`} className="w-full h-full object-cover rounded-lg" />
                ) : (
                  <div className="text-center">
                    <div className="text-4xl mb-2">🎨</div>
                    <p className="text-xs text-[rgb(var(--text-tertiary))]">生成中...</p>
                  </div>
                )}
              </div>
              <p className="text-xs text-[rgb(var(--text-secondary))]">{image.prompt || `シーン ${index + 1}`}</p>
            </div>
          )) || (
            <div className="col-span-2 text-center py-8">
              <p className="text-[rgb(var(--text-tertiary))]">画像生成準備中...</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Phase 6: セリフ配置
function Phase6DialoguePreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">セリフ・効果音配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          {data?.dialogues?.map((dialogue: any, index: number) => (
            <div key={index} className="flex gap-3 items-start">
              <div className="w-8 h-8 bg-[rgb(var(--accent-primary))] rounded-full flex items-center justify-center text-white text-xs">
                {dialogue.panelNumber || index + 1}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium">{dialogue.character || 'ナレーション'}</span>
                  <Badge variant="outline" className="text-xs">{dialogue.type || 'セリフ'}</Badge>
                </div>
                <p className="text-sm bg-[rgb(var(--bg-primary))] rounded-lg p-2">
                  {dialogue.text || '...'}
                </p>
              </div>
            </div>
          )) || <p className="text-[rgb(var(--text-tertiary))]">セリフ配置中...</p>}
        </div>
        <div className="pt-3 border-t border-[rgb(var(--border-default))]">
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">効果音</h4>
          <div className="flex flex-wrap gap-2">
            {data?.soundEffects?.map((se: string, index: number) => (
              <Badge key={index} variant="secondary">{se}</Badge>
            )) || <Badge variant="outline">効果音なし</Badge>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Phase 7: 最終統合・品質調整
function Phase7IntegrationPreview({ data }: { data: any }) {
  return (
    <Card className="border-[rgb(var(--border-default))] bg-[rgb(var(--bg-secondary))]">
      <CardHeader>
        <CardTitle className="text-lg">最終統合結果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">品質スコア</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-xs">ストーリー完成度</span>
                <span className="text-sm font-medium">{data?.qualityScores?.story || '0'}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs">画像品質</span>
                <span className="text-sm font-medium">{data?.qualityScores?.visual || '0'}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs">レイアウト</span>
                <span className="text-sm font-medium">{data?.qualityScores?.layout || '0'}%</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">統計情報</h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span>総ページ数</span>
                <span>{data?.stats?.totalPages || '0'}</span>
              </div>
              <div className="flex justify-between">
                <span>総コマ数</span>
                <span>{data?.stats?.totalPanels || '0'}</span>
              </div>
              <div className="flex justify-between">
                <span>生成時間</span>
                <span>{data?.stats?.generationTime || '0'}秒</span>
              </div>
            </div>
          </div>
        </div>
        <div className="pt-3 border-t border-[rgb(var(--border-default))]">
          <h4 className="text-sm font-semibold text-[rgb(var(--text-secondary))] mb-2">最終出力</h4>
          {data?.outputUrl ? (
            <a href={data.outputUrl} className="text-[rgb(var(--accent-primary))] hover:underline text-sm">
              ダウンロード可能
            </a>
          ) : (
            <p className="text-sm text-[rgb(var(--text-tertiary))]">統合処理中...</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}