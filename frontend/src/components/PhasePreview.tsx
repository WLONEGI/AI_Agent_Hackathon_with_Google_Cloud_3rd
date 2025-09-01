'use client';

import { useState, useEffect } from 'react';

interface PreviewData {
  type: string;
  content: any;
  timestamp?: number;
}

interface PhasePreviewProps {
  phaseId: number;
  phaseName: string;
  preview?: PreviewData;
}

export default function PhasePreview({ phaseId, phaseName, preview }: PhasePreviewProps) {
  if (!preview) {
    return (
      <div className="w-full h-48 bg-[#0f0f0f] border border-white/5 rounded-lg flex items-center justify-center">
        <span className="text-white/20 text-xs">プレビュー待機中...</span>
      </div>
    );
  }

  // Render different preview types based on phase
  const renderPreview = () => {
    switch (phaseId) {
      case 1: // コンセプト・世界観分析
        return (
          <div className="p-4 space-y-2">
            <div className="text-xs text-white/40">世界観・テーマ</div>
            <div className="flex flex-wrap gap-2">
              {preview.content.themes?.map((theme: string, index: number) => (
                <span key={index} className="px-2 py-1 bg-white/5 text-white/60 text-xs rounded">
                  {theme}
                </span>
              ))}
            </div>
            {preview.content.worldSetting && (
              <>
                <div className="text-xs text-white/40 mt-3">世界観設定</div>
                <p className="text-xs text-white/50 leading-relaxed">{preview.content.worldSetting}</p>
              </>
            )}
            {preview.content.genre && (
              <>
                <div className="text-xs text-white/40 mt-3">ジャンル</div>
                <p className="text-xs text-white/60">{preview.content.genre}</p>
              </>
            )}
          </div>
        );

      case 2: // キャラクター設定
        return (
          <div className="p-4">
            {preview.content.imageUrl ? (
              <img 
                src={preview.content.imageUrl} 
                alt="Character design" 
                className="w-full h-auto rounded opacity-80"
              />
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {preview.content.characters?.map((char: any, index: number) => (
                  <div key={index} className="bg-white/5 p-3 rounded">
                    <div className="text-xs text-white/70 font-medium">{char.name}</div>
                    <div className="text-xs text-white/50">{char.role}</div>
                    {char.appearance && (
                      <div className="text-xs text-white/40 mt-1">{char.appearance}</div>
                    )}
                    {char.personality && (
                      <div className="text-xs text-white/40 mt-1">性格: {char.personality}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 3: // プロット・ストーリー構成
        return (
          <div className="p-4 space-y-3">
            {preview.content.acts?.map((act: any, index: number) => (
              <div key={index} className="border-l-2 border-white/10 pl-3">
                <div className="text-xs text-white/60 font-medium">第{index + 1}幕: {act.title}</div>
                <p className="text-xs text-white/40 mt-1">{act.description}</p>
                {act.scenes && (
                  <div className="mt-2 space-y-1">
                    {act.scenes.map((scene: any, sceneIndex: number) => (
                      <div key={sceneIndex} className="text-xs text-white/30 pl-2">• {scene}</div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        );

      case 4: // ネーム生成
        return (
          <div className="p-4">
            <div className="text-xs text-white/40 mb-3">コマ構成</div>
            {preview.content.panels?.map((panel: any, index: number) => (
              <div key={index} className="mb-3 border border-white/10 rounded">
                <div className="text-xs text-white/60 px-2 py-1 bg-white/5">Panel {index + 1}</div>
                <div className="p-2">
                  <div className="text-xs text-white/50 mb-1">{panel.description}</div>
                  {panel.composition && (
                    <div className="text-xs text-white/40">構図: {panel.composition}</div>
                  )}
                  {panel.characters && (
                    <div className="text-xs text-white/40">キャラ: {panel.characters.join(', ')}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        );

      case 5: // シーン画像生成
        return (
          <div className="p-4">
            <div className="text-xs text-white/40 mb-3">生成画像</div>
            {preview.content.images?.map((image: any, index: number) => (
              <div key={index} className="mb-3">
                <div className="text-xs text-white/60 mb-1">Scene {index + 1}</div>
                {image.url ? (
                  <img 
                    src={image.url} 
                    alt={`Generated scene ${index + 1}`} 
                    className="w-full h-auto rounded opacity-90"
                  />
                ) : (
                  <div className="aspect-video bg-white/5 rounded flex items-center justify-center">
                    <span className="text-white/30 text-xs">画像生成中...</span>
                  </div>
                )}
                {image.prompt && (
                  <div className="text-xs text-white/30 mt-1">Prompt: {image.prompt}</div>
                )}
              </div>
            ))}
          </div>
        );

      case 6: // セリフ配置
        return (
          <div className="p-4 space-y-3">
            <div className="text-xs text-white/40">セリフ・吹き出し配置</div>
            {preview.content.dialogues?.map((dialogue: any, index: number) => (
              <div key={index} className="bg-white/5 p-2 rounded">
                <div className="flex items-start gap-2">
                  <span className="text-xs text-white/50 font-medium">{dialogue.character}:</span>
                  <span className="text-xs text-white/70 italic flex-1">"{dialogue.text}"</span>
                </div>
                {dialogue.position && (
                  <div className="text-xs text-white/30 mt-1">位置: {dialogue.position}</div>
                )}
                {dialogue.style && (
                  <div className="text-xs text-white/30">スタイル: {dialogue.style}</div>
                )}
              </div>
            ))}
            {preview.content.soundEffects && (
              <>
                <div className="text-xs text-white/40 mt-4">効果音</div>
                <div className="flex flex-wrap gap-2">
                  {preview.content.soundEffects.map((effect: string, index: number) => (
                    <span key={index} className="px-2 py-1 bg-yellow-500/10 text-yellow-400/70 text-xs rounded">
                      {effect}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        );

      case 7: // 最終統合・品質調整
        return (
          <div className="p-4">
            <div className="text-xs text-white/40 mb-3">最終レイアウト</div>
            {preview.content.finalPages ? (
              <div className="space-y-3">
                {preview.content.finalPages.map((page: any, index: number) => (
                  <div key={index} className="border border-white/10 rounded">
                    <div className="text-xs text-white/50 px-2 py-1 bg-white/5">Page {index + 1}</div>
                    {page.imageUrl ? (
                      <img 
                        src={page.imageUrl} 
                        alt={`Final page ${index + 1}`} 
                        className="w-full h-auto rounded-b"
                      />
                    ) : (
                      <div className="aspect-[3/4] bg-white/5 flex items-center justify-center">
                        <span className="text-white/30 text-xs">統合中...</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-white/50">品質調整項目:</div>
                {preview.content.qualityChecks?.map((check: any, index: number) => (
                  <div key={index} className="flex items-center gap-2">
                    <span className={`material-symbols-outlined text-xs ${
                      check.status === 'completed' ? 'text-green-400' : 
                      check.status === 'processing' ? 'text-yellow-400' : 'text-white/20'
                    }`}>
                      {check.status === 'completed' ? 'check_circle' : 
                       check.status === 'processing' ? 'pending' : 'radio_button_unchecked'}
                    </span>
                    <span className="text-xs text-white/50">{check.item}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="p-4">
            <pre className="text-xs text-white/40">{JSON.stringify(preview.content, null, 2)}</pre>
          </div>
        );
    }
  };

  return (
    <div className="w-full bg-[#0f0f0f] border border-white/5 rounded-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
        <span className="text-xs text-white/40">{phaseName} プレビュー</span>
        {preview.timestamp && (
          <span className="text-xs text-white/20 font-mono">
            {new Date(preview.timestamp).toLocaleTimeString('ja-JP')}
          </span>
        )}
      </div>
      <div className="max-h-64 overflow-y-auto">
        {renderPreview()}
      </div>
    </div>
  );
}