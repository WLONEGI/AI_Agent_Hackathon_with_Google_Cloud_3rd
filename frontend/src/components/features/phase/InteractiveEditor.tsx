'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { type PhaseId } from '@/types/processing';
import { 
  Move, 
  Type, 
  Image, 
  Trash2, 
  Plus, 
  Save,
  Undo,
  Redo,
  ZoomIn,
  ZoomOut,
  Grid
} from 'lucide-react';

interface InteractiveEditorProps {
  phaseId: PhaseId;
  data: any;
  onSave: (updatedData: any) => void;
  onCancel: () => void;
}

interface EditableElement {
  id: string;
  type: 'text' | 'image' | 'panel' | 'character';
  position: { x: number; y: number };
  size: { width: number; height: number };
  content: any;
  locked?: boolean;
}

export function InteractiveEditor({ phaseId, data, onSave, onCancel }: InteractiveEditorProps) {
  const [elements, setElements] = useState<EditableElement[]>([]);
  const [selectedElement, setSelectedElement] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
  const [history, setHistory] = useState<any[]>([]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const canvasRef = useRef<HTMLDivElement>(null);

  // フェーズごとの編集可能要素を初期化
  useEffect(() => {
    const initElements = () => {
      switch (phaseId) {
        case 1: // コンセプト・世界観
          return convertConceptToElements(data);
        case 2: // キャラクター設定
          return convertCharactersToElements(data);
        case 3: // プロット構成
          return convertPlotToElements(data);
        case 4: // ネーム生成
          return convertNameToElements(data);
        case 5: // 画像生成
          return convertImagesToElements(data);
        case 6: // セリフ配置
          return convertDialoguesToElements(data);
        case 7: // 最終統合
          return convertFinalToElements(data);
        default:
          return [];
      }
    };
    
    const initialElements = initElements();
    setElements(initialElements);
    addToHistory(initialElements);
  }, [phaseId, data]);

  // ドラッグ&ドロップ処理
  const handleMouseDown = (e: React.MouseEvent, elementId: string) => {
    if (e.button !== 0) return; // 左クリックのみ
    
    const element = elements.find(el => el.id === elementId);
    if (!element || element.locked) return;
    
    setSelectedElement(elementId);
    setIsDragging(true);
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      setDragOffset({
        x: (e.clientX - rect.left) / scale - element.position.x,
        y: (e.clientY - rect.top) / scale - element.position.y
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !selectedElement) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      const newX = (e.clientX - rect.left) / scale - dragOffset.x;
      const newY = (e.clientY - rect.top) / scale - dragOffset.y;
      
      updateElementPosition(selectedElement, newX, newY);
    }
  };

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      addToHistory(elements);
    }
  };

  // 要素の位置更新
  const updateElementPosition = (elementId: string, x: number, y: number) => {
    setElements(prev => prev.map(el => 
      el.id === elementId ? { ...el, position: { x, y } } : el
    ));
  };

  // 要素のサイズ変更
  const updateElementSize = (elementId: string, width: number, height: number) => {
    setElements(prev => prev.map(el => 
      el.id === elementId ? { ...el, size: { width, height } } : el
    ));
    addToHistory(elements);
  };

  // テキスト編集
  const updateElementContent = (elementId: string, content: any) => {
    setElements(prev => prev.map(el => 
      el.id === elementId ? { ...el, content } : el
    ));
    addToHistory(elements);
  };

  // 要素の削除
  const deleteElement = (elementId: string) => {
    setElements(prev => prev.filter(el => el.id !== elementId));
    setSelectedElement(null);
    addToHistory(elements);
  };

  // 要素の追加
  const addElement = (type: EditableElement['type']) => {
    const newElement: EditableElement = {
      id: `element-${Date.now()}`,
      type,
      position: { x: 100, y: 100 },
      size: { width: 200, height: 100 },
      content: type === 'text' ? 'New Text' : null,
      locked: false
    };
    setElements(prev => [...prev, newElement]);
    addToHistory(elements);
  };

  // 履歴管理
  const addToHistory = (state: EditableElement[]) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(JSON.parse(JSON.stringify(state)));
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setElements(JSON.parse(JSON.stringify(history[historyIndex - 1])));
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setElements(JSON.parse(JSON.stringify(history[historyIndex + 1])));
    }
  };

  // 保存処理
  const handleSave = () => {
    const updatedData = convertElementsToData(elements, phaseId);
    onSave(updatedData);
  };

  return (
    <div className="flex flex-col h-full bg-[rgb(var(--bg-primary))]">
      {/* ツールバー */}
      <div className="flex items-center justify-between p-3 border-b border-[rgb(var(--border-default))]">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => addElement('text')}>
            <Type className="w-4 h-4 mr-1" />
            テキスト追加
          </Button>
          <Button size="sm" variant="outline" onClick={() => addElement('image')}>
            <Image className="w-4 h-4 mr-1" />
            画像追加
          </Button>
          <Button size="sm" variant="outline" onClick={() => addElement('panel')}>
            <Grid className="w-4 h-4 mr-1" />
            パネル追加
          </Button>
          <div className="border-l border-[rgb(var(--border-default))] mx-2 h-6" />
          <Button size="sm" variant="outline" onClick={undo} disabled={historyIndex === 0}>
            <Undo className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={redo} disabled={historyIndex === history.length - 1}>
            <Redo className="w-4 h-4" />
          </Button>
          <div className="border-l border-[rgb(var(--border-default))] mx-2 h-6" />
          <Button size="sm" variant="outline" onClick={() => setScale(Math.min(scale + 0.1, 2))}>
            <ZoomIn className="w-4 h-4" />
          </Button>
          <span className="text-xs text-[rgb(var(--text-secondary))] px-2">{Math.round(scale * 100)}%</span>
          <Button size="sm" variant="outline" onClick={() => setScale(Math.max(scale - 0.1, 0.5))}>
            <ZoomOut className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={onCancel}>
            キャンセル
          </Button>
          <Button size="sm" onClick={handleSave}>
            <Save className="w-4 h-4 mr-1" />
            保存
          </Button>
        </div>
      </div>

      {/* キャンバス */}
      <div 
        ref={canvasRef}
        className="flex-1 relative overflow-auto bg-[rgb(var(--bg-secondary))]"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >
        <div 
          className="relative min-h-full"
          style={{
            transform: `scale(${scale})`,
            transformOrigin: 'top left',
            width: `${100 / scale}%`,
            height: `${100 / scale}%`
          }}
        >
          {elements.map(element => (
            <EditableElement
              key={element.id}
              element={element}
              isSelected={selectedElement === element.id}
              onMouseDown={(e) => handleMouseDown(e, element.id)}
              onDelete={() => deleteElement(element.id)}
              onContentChange={(content) => updateElementContent(element.id, content)}
            />
          ))}
        </div>
      </div>

      {/* プロパティパネル */}
      {selectedElement && (
        <div className="border-t border-[rgb(var(--border-default))] p-3 bg-[rgb(var(--bg-tertiary))]">
          <ElementProperties
            element={elements.find(el => el.id === selectedElement)!}
            onPositionChange={(x, y) => updateElementPosition(selectedElement, x, y)}
            onSizeChange={(w, h) => updateElementSize(selectedElement, w, h)}
          />
        </div>
      )}
    </div>
  );
}

// 編集可能要素コンポーネント
function EditableElement({ 
  element, 
  isSelected, 
  onMouseDown, 
  onDelete, 
  onContentChange 
}: {
  element: EditableElement;
  isSelected: boolean;
  onMouseDown: (e: React.MouseEvent) => void;
  onDelete: () => void;
  onContentChange: (content: any) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(element.content);

  const handleDoubleClick = () => {
    if (element.type === 'text') {
      setIsEditing(true);
    }
  };

  const handleBlur = () => {
    setIsEditing(false);
    onContentChange(editContent);
  };

  return (
    <div
      className={`absolute border-2 ${
        isSelected ? 'border-[rgb(var(--accent-primary))]' : 'border-transparent'
      } hover:border-[rgb(var(--border-default))] transition-colors`}
      style={{
        left: element.position.x,
        top: element.position.y,
        width: element.size.width,
        height: element.size.height,
        cursor: element.locked ? 'not-allowed' : 'move'
      }}
      onMouseDown={onMouseDown}
      onDoubleClick={handleDoubleClick}
    >
      {/* 削除ボタン */}
      {isSelected && !element.locked && (
        <Button
          size="icon"
          variant="destructive"
          className="absolute -top-2 -right-2 w-6 h-6"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
        >
          <Trash2 className="w-3 h-3" />
        </Button>
      )}

      {/* コンテンツ */}
      {element.type === 'text' && (
        isEditing ? (
          <textarea
            className="w-full h-full p-2 bg-transparent resize-none outline-none"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            onBlur={handleBlur}
            autoFocus
          />
        ) : (
          <div className="p-2">{element.content}</div>
        )
      )}
      
      {element.type === 'image' && (
        <div className="w-full h-full bg-[rgb(var(--bg-primary))] flex items-center justify-center">
          <Image className="w-8 h-8 text-[rgb(var(--text-tertiary))]" />
        </div>
      )}
      
      {element.type === 'panel' && (
        <div className="w-full h-full border border-[rgb(var(--border-default))] bg-white/5" />
      )}
    </div>
  );
}

// プロパティパネル
function ElementProperties({ 
  element, 
  onPositionChange, 
  onSizeChange 
}: {
  element: EditableElement;
  onPositionChange: (x: number, y: number) => void;
  onSizeChange: (width: number, height: number) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-3 text-sm">
      <div>
        <label className="text-[rgb(var(--text-secondary))]">位置 X</label>
        <input
          type="number"
          className="w-full px-2 py-1 bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded"
          value={Math.round(element.position.x)}
          onChange={(e) => onPositionChange(Number(e.target.value), element.position.y)}
        />
      </div>
      <div>
        <label className="text-[rgb(var(--text-secondary))]">位置 Y</label>
        <input
          type="number"
          className="w-full px-2 py-1 bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded"
          value={Math.round(element.position.y)}
          onChange={(e) => onPositionChange(element.position.x, Number(e.target.value))}
        />
      </div>
      <div>
        <label className="text-[rgb(var(--text-secondary))]">幅</label>
        <input
          type="number"
          className="w-full px-2 py-1 bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded"
          value={Math.round(element.size.width)}
          onChange={(e) => onSizeChange(Number(e.target.value), element.size.height)}
        />
      </div>
      <div>
        <label className="text-[rgb(var(--text-secondary))]">高さ</label>
        <input
          type="number"
          className="w-full px-2 py-1 bg-[rgb(var(--bg-primary))] border border-[rgb(var(--border-default))] rounded"
          value={Math.round(element.size.height)}
          onChange={(e) => onSizeChange(element.size.width, Number(e.target.value))}
        />
      </div>
    </div>
  );
}

// ヘルパー関数（データ変換）
function convertConceptToElements(data: any): EditableElement[] {
  const elements: EditableElement[] = [];
  
  if (data?.theme) {
    elements.push({
      id: 'theme',
      type: 'text',
      position: { x: 20, y: 20 },
      size: { width: 300, height: 60 },
      content: data.theme,
      locked: false
    });
  }
  
  if (data?.worldSetting) {
    elements.push({
      id: 'worldSetting',
      type: 'text',
      position: { x: 20, y: 100 },
      size: { width: 400, height: 100 },
      content: data.worldSetting,
      locked: false
    });
  }
  
  return elements;
}

function convertCharactersToElements(data: any): EditableElement[] {
  const elements: EditableElement[] = [];
  
  data?.characters?.forEach((char: any, index: number) => {
    elements.push({
      id: `char-${index}`,
      type: 'character',
      position: { x: 20 + (index % 3) * 220, y: 20 + Math.floor(index / 3) * 300 },
      size: { width: 200, height: 280 },
      content: char,
      locked: false
    });
  });
  
  return elements;
}

function convertPlotToElements(data: any): EditableElement[] {
  const elements: EditableElement[] = [];
  
  ['act1', 'act2', 'act3'].forEach((act, index) => {
    if (data?.[act]) {
      elements.push({
        id: act,
        type: 'text',
        position: { x: 20, y: 20 + index * 150 },
        size: { width: 400, height: 120 },
        content: data[act],
        locked: false
      });
    }
  });
  
  return elements;
}

function convertNameToElements(data: any): EditableElement[] {
  const elements: EditableElement[] = [];
  
  data?.pages?.forEach((page: any, pageIndex: number) => {
    page.panels?.forEach((panel: any, panelIndex: number) => {
      elements.push({
        id: `panel-${pageIndex}-${panelIndex}`,
        type: 'panel',
        position: { 
          x: 20 + (panelIndex % 3) * 180, 
          y: 20 + pageIndex * 400 + Math.floor(panelIndex / 3) * 180 
        },
        size: { width: 160, height: 160 },
        content: panel,
        locked: false
      });
    });
  });
  
  return elements;
}

function convertImagesToElements(data: any): EditableElement[] {
  const elements: EditableElement[] = [];
  
  data?.images?.forEach((image: any, index: number) => {
    elements.push({
      id: `image-${index}`,
      type: 'image',
      position: { x: 20 + (index % 2) * 320, y: 20 + Math.floor(index / 2) * 240 },
      size: { width: 300, height: 220 },
      content: image,
      locked: false
    });
  });
  
  return elements;
}

function convertDialoguesToElements(data: any): EditableElement[] {
  const elements: EditableElement[] = [];
  
  data?.dialogues?.forEach((dialogue: any, index: number) => {
    elements.push({
      id: `dialogue-${index}`,
      type: 'text',
      position: { x: 20 + (index % 2) * 250, y: 20 + Math.floor(index / 2) * 100 },
      size: { width: 230, height: 80 },
      content: dialogue.text,
      locked: false
    });
  });
  
  return elements;
}

function convertFinalToElements(data: any): EditableElement[] {
  // 最終統合は全体のレイアウト調整
  return [];
}

function convertElementsToData(elements: EditableElement[], phaseId: PhaseId): any {
  // 要素をデータ形式に変換して返す
  const data: any = {};
  
  switch (phaseId) {
    case 1: // コンセプト・世界観
      const themeEl = elements.find(el => el.id === 'theme');
      const worldEl = elements.find(el => el.id === 'worldSetting');
      if (themeEl) data.theme = themeEl.content;
      if (worldEl) data.worldSetting = worldEl.content;
      break;
      
    case 2: // キャラクター設定
      data.characters = elements
        .filter(el => el.type === 'character')
        .sort((a, b) => a.position.x - b.position.x)
        .map(el => el.content);
      break;
      
    case 3: // プロット構成
      const act1El = elements.find(el => el.id === 'act1');
      const act2El = elements.find(el => el.id === 'act2');
      const act3El = elements.find(el => el.id === 'act3');
      if (act1El) data.act1 = act1El.content;
      if (act2El) data.act2 = act2El.content;
      if (act3El) data.act3 = act3El.content;
      break;
      
    case 4: // ネーム生成
      const panels = elements
        .filter(el => el.type === 'panel')
        .sort((a, b) => {
          const [aPage, aPanel] = a.id.split('-').slice(1).map(Number);
          const [bPage, bPanel] = b.id.split('-').slice(1).map(Number);
          return aPage !== bPage ? aPage - bPage : aPanel - bPanel;
        });
      
      const pages: any[] = [];
      panels.forEach(panel => {
        const [pageIndex] = panel.id.split('-').slice(1).map(Number);
        if (!pages[pageIndex]) {
          pages[pageIndex] = { panels: [] };
        }
        pages[pageIndex].panels.push(panel.content);
      });
      data.pages = pages.filter(Boolean);
      break;
      
    case 5: // 画像生成
      data.images = elements
        .filter(el => el.type === 'image')
        .sort((a, b) => {
          const aIndex = parseInt(a.id.split('-')[1]);
          const bIndex = parseInt(b.id.split('-')[1]);
          return aIndex - bIndex;
        })
        .map(el => el.content);
      break;
      
    case 6: // セリフ配置
      data.dialogues = elements
        .filter(el => el.type === 'text' && el.id.startsWith('dialogue-'))
        .sort((a, b) => {
          const aIndex = parseInt(a.id.split('-')[1]);
          const bIndex = parseInt(b.id.split('-')[1]);
          return aIndex - bIndex;
        })
        .map(el => ({
          text: el.content,
          position: el.position,
          size: el.size
        }));
      break;
      
    case 7: // 最終統合
      // 全要素の位置とサイズ情報を保存
      data.layout = elements.map(el => ({
        id: el.id,
        type: el.type,
        position: el.position,
        size: el.size,
        content: el.content
      }));
      break;
  }
  
  return data;
}