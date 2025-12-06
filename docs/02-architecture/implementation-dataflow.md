---
document_id: "ARCH-DATAFLOW-001"
title: "データフロー実装仕様書"
version: "1.0"
date_created: "2025-10-01"
date_updated: "2025-10-01"
status: "active"
category: "architecture"
document_type: "implementation-specification"
tags: ["dataflow", "websocket", "state-management", "data-transformation", "real-time"]
parent_doc: "ARCH-README-001"
related_docs: ["ARCH-SYS-001", "API-OVERVIEW-001", "UI-JOURNEY-001"]
target_audience: ["backend-developer", "frontend-developer", "system-architect"]
stakeholders:
  author: "Claude Code"
  approver: "根岸祐樹"
---

# データフロー実装仕様書

> **TL;DR**: データ変換ロジック、WebSocket双方向通信、ステート管理の実装仕様。7フェーズ間のデータ変換パイプライン、WebSocketメッセージフォーマット（6種類）、フロントエンド/バックエンドステート管理パターン、キャッシュ戦略を定義。

## 目次

- [1. データ変換パイプライン](#1-データ変換パイプライン)
- [2. WebSocket通信実装](#2-websocket通信実装)
- [3. ステート管理](#3-ステート管理)
- [4. キャッシュ戦略](#4-キャッシュ戦略)

---

## 1. データ変換パイプライン

### 1.1 フェーズ間データ変換

#### Phase 1 → Phase 2 変換
```python
def transform_concept_to_character_input(concept_output: Phase1Output) -> Phase2Input:
    """コンセプト分析結果をキャラクター設計入力に変換"""
    return Phase2Input(
        concept=concept_output.concept,
        genre=concept_output.genre,
        target_audience=concept_output.target_audience,
        world_setting=concept_output.world_setting,
        character_seeds=extract_character_hints(concept_output.summary)
    )

def extract_character_hints(summary: str) -> list[CharacterSeed]:
    """サマリーテキストからキャラクターヒントを抽出"""
    # 正規表現または簡易NLPでキャラクター名・特徴を抽出
    pass
```

#### Phase 2 → Phase 3 変換
```python
def transform_character_to_plot_input(
    concept: Phase1Output,
    characters: Phase2Output
) -> Phase3Input:
    """キャラクター設計をプロット入力に統合"""
    return Phase3Input(
        concept=concept.concept,
        characters=characters.characters,
        relationships=build_relationship_matrix(characters.characters),
        plot_constraints={
            "page_count": concept.estimated_pages,
            "tone": concept.tone,
            "themes": concept.themes
        }
    )
```

#### Phase 4 → Phase 5 変換（並列処理対応）
```python
async def transform_layout_to_scene_inputs(
    layout: Phase4Output
) -> list[Phase5Input]:
    """ネーム構成を並列画像生成入力に分割"""
    scene_inputs = []

    for page in layout.pages:
        for panel in page.panels:
            scene_input = Phase5Input(
                panel_id=panel.id,
                scene_description=panel.scene_description,
                characters=[c.id for c in panel.characters],
                visual_style=layout.visual_style,
                composition=panel.composition,
                camera_angle=panel.camera_angle
            )
            scene_inputs.append(scene_input)

    return scene_inputs

# 並列実行
async def process_phase5_parallel(inputs: list[Phase5Input]):
    """Phase 5を並列実行"""
    tasks = [generate_scene_image(inp) for inp in inputs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### 1.2 データシリアライゼーション

#### Pydantic モデル定義例
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PhaseOutput(BaseModel):
    """全フェーズ共通出力ベース"""
    phase_number: int = Field(..., ge=1, le=7)
    session_id: str
    timestamp: datetime
    quality_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int
    metadata: dict[str, any] = {}

class Phase1Output(PhaseOutput):
    """Phase 1固有出力"""
    concept: ConceptData
    genre: GenreData
    target_audience: AudienceData
    world_setting: WorldSettingData
    estimated_pages: int
    tone: str

class Phase5Output(PhaseOutput):
    """Phase 5固有出力"""
    panels: list[PanelImage]

    class PanelImage(BaseModel):
        panel_id: str
        image_url: str  # Cloud Storage署名付きURL
        thumbnail_url: str
        generation_params: dict
        quality_metrics: ImageQualityMetrics
```

---

## 2. WebSocket通信実装

### 2.1 接続確立

#### バックエンド (FastAPI)
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: dict):
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_client_message(session_id, data)
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

#### フロントエンド (TypeScript)
```typescript
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(sessionId: string, token: string) {
    const wsUrl = `${WS_BASE_URL}/ws/session/${sessionId}?token=${token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      this.attemptReconnect(sessionId, token);
    };
  }

  private attemptReconnect(sessionId: string, token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * (2 ** this.reconnectAttempts), 30000);
      setTimeout(() => this.connect(sessionId, token), delay);
    }
  }

  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### 2.2 メッセージフォーマット

#### Server → Client メッセージ

**1. フェーズ進行通知**
```json
{
  "type": "phase_progress",
  "data": {
    "phase": 1,
    "progress": 45,
    "status": "processing",
    "message": "コンセプト分析中...",
    "estimated_remaining_seconds": 30
  },
  "timestamp": "2025-01-20T10:30:00Z"
}
```

**2. フェーズ完了通知**
```json
{
  "type": "phase_complete",
  "data": {
    "phase": 1,
    "quality_score": 0.87,
    "preview_url": "https://storage.googleapis.com/...",
    "next_phase": 2
  },
  "timestamp": "2025-01-20T10:31:00Z"
}
```

**3. フィードバック待機通知**
```json
{
  "type": "feedback_waiting",
  "data": {
    "phase": 2,
    "preview_data": {
      "type": "character_profiles",
      "content": {...},
      "thumbnail": "https://..."
    },
    "feedback_options": ["brighter", "serious", "detailed", "simple"],
    "timeout_seconds": 1800
  },
  "timestamp": "2025-01-20T10:32:00Z"
}
```

**4. エラー通知**
```json
{
  "type": "error",
  "data": {
    "code": "AI_001",
    "message": "AI生成APIエラー",
    "phase": 3,
    "retry_available": true,
    "details": "Rate limit exceeded"
  },
  "timestamp": "2025-01-20T10:35:00Z"
}
```

#### Client → Server メッセージ

**1. HITLフィードバック**
```json
{
  "type": "user_feedback",
  "data": {
    "phase": 2,
    "feedback_type": "natural_language",
    "content": "もっと若々しいキャラクターにして",
    "quick_option": null
  },
  "timestamp": "2025-01-20T10:33:00Z"
}
```

**2. スキップ**
```json
{
  "type": "skip_feedback",
  "data": {
    "phase": 3
  },
  "timestamp": "2025-01-20T10:36:00Z"
}
```

**3. キャンセルリクエスト**
```json
{
  "type": "cancel_generation",
  "data": {
    "session_id": "uuid",
    "reason": "user_requested"
  },
  "timestamp": "2025-01-20T10:40:00Z"
}
```

### 2.3 ハートビート実装

```python
# Backend
async def send_heartbeat(session_id: str):
    while session_id in manager.active_connections:
        await manager.send_message(session_id, {"type": "heartbeat"})
        await asyncio.sleep(30)

# Frontend
private heartbeatInterval: number | null = null;

startHeartbeat() {
  this.heartbeatInterval = window.setInterval(() => {
    this.send({ type: "ping" });
  }, 25000); // 25秒ごと
}
```

---

## 3. ステート管理

### 3.1 バックエンドステート管理

#### セッションステート（PostgreSQL）
```python
class SessionState:
    """データベース永続化されるセッション状態"""
    session_id: str
    user_id: str
    status: SessionStatus  # queued, running, completed, failed
    current_phase: int
    phase_results: dict[int, PhaseOutput]
    feedback_history: list[FeedbackEntry]
    created_at: datetime
    updated_at: datetime

# SQLAlchemy モデル
class MangaSession(Base):
    __tablename__ = "manga_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(Enum(SessionStatus))
    current_phase = Column(Integer, default=0)
    phase_status = Column(JSONB)  # {1: "completed", 2: "running", ...}
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # リレーション
    phase_results = relationship("PhaseResult", back_populates="session")
    feedback_entries = relationship("UserFeedback", back_populates="session")
```

#### インメモリステート（処理中）
```python
from dataclasses import dataclass, field

@dataclass
class ProcessingState:
    """処理中の一時的な状態（インメモリ）"""
    session_id: str
    phase_outputs: dict[int, any] = field(default_factory=dict)
    accumulated_context: dict = field(default_factory=dict)
    retry_counts: dict[int, int] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)

    def add_phase_output(self, phase: int, output: any):
        self.phase_outputs[phase] = output
        self.accumulated_context[f"phase_{phase}"] = output.dict()

    def get_context_for_phase(self, phase: int) -> dict:
        """特定フェーズに必要なコンテキストを取得"""
        return {
            k: v for k, v in self.accumulated_context.items()
            if int(k.split("_")[1]) < phase
        }
```

### 3.2 フロントエンドステート管理

#### React Context + Hooks
```typescript
// Context定義
interface GenerationState {
  sessionId: string | null;
  phases: PhaseState[];
  currentPhase: number;
  overallStatus: 'idle' | 'generating' | 'waiting_feedback' | 'completed' | 'error';
  error: ErrorInfo | null;
}

interface PhaseState {
  phaseNumber: number;
  status: 'pending' | 'processing' | 'feedback_waiting' | 'completed';
  progress: number;
  previewData: any | null;
  qualityScore: number | null;
}

// Context実装
const GenerationContext = createContext<{
  state: GenerationState;
  actions: GenerationActions;
} | null>(null);

export function GenerationProvider({ children }) {
  const [state, setState] = useState<GenerationState>(initialState);

  const actions = {
    startGeneration: async (inputText: string) => {
      const response = await fetch('/api/v1/manga/generate', {
        method: 'POST',
        body: JSON.stringify({ text: inputText })
      });
      const { session_id } = await response.json();
      setState(prev => ({ ...prev, sessionId: session_id }));

      // WebSocket接続開始
      connectWebSocket(session_id);
    },

    submitFeedback: async (phase: number, feedback: string) => {
      wsClient.send({
        type: 'user_feedback',
        data: { phase, feedback_type: 'natural_language', content: feedback }
      });
    },

    updatePhaseProgress: (phase: number, progress: number) => {
      setState(prev => ({
        ...prev,
        phases: prev.phases.map(p =>
          p.phaseNumber === phase ? { ...p, progress } : p
        )
      }));
    }
  };

  return (
    <GenerationContext.Provider value={{ state, actions }}>
      {children}
    </GenerationContext.Provider>
  );
}

// カスタムフック
export function useGeneration() {
  const context = useContext(GenerationContext);
  if (!context) throw new Error('useGeneration must be used within GenerationProvider');
  return context;
}
```

---

## 4. キャッシュ戦略

### 4.1 プレビュー画像キャッシュ

#### Cloud Storage + 署名付きURL
```python
from google.cloud import storage
from datetime import timedelta

class PreviewCache:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def store_preview(
        self,
        session_id: str,
        phase: int,
        data: bytes,
        content_type: str = "application/json"
    ) -> str:
        """プレビューデータをCloud Storageに保存"""
        blob_name = f"previews/{session_id}/phase_{phase}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(data, content_type=content_type)

        # 署名付きURL生成（1時間有効）
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET"
        )
        return url

    def cleanup_expired(self):
        """期限切れプレビューを削除（定期実行）"""
        cutoff = datetime.now() - timedelta(hours=24)
        blobs = self.bucket.list_blobs(prefix="previews/")

        for blob in blobs:
            if blob.time_created < cutoff:
                blob.delete()
```

#### フロントエンドキャッシュ
```typescript
// Service Worker でのキャッシュ
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('storage.googleapis.com')) {
    event.respondWith(
      caches.open('preview-cache').then((cache) => {
        return cache.match(event.request).then((response) => {
          return response || fetch(event.request).then((fetchResponse) => {
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          });
        });
      })
    );
  }
});
```

### 4.2 API応答キャッシュ

```python
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=128)
def get_session_status(session_id: str) -> Optional[SessionStatus]:
    """セッションステータスをキャッシュ（60秒TTL）"""
    # キャッシュキーにタイムスタンプを含めて疑似TTL実装
    cache_key = f"{session_id}_{int(time.time() // 60)}"
    return _fetch_session_status(cache_key)
```

---

## 関連文書

- [技術仕様書](./technical-spec.md)
- [エラーハンドリング仕様](./error-handling-spec.md)
- [WebSocket API設計](../03-api/api-overview.md#6-websocket統合仕様)
- [HITLシステム設計](../06-ai/hitl-system.md)

---

## 改訂履歴

| 版数 | 日付 | 変更内容 | 担当者 |
|------|------|----------|--------|
| 1.0 | 2025-10-01 | 初版作成 | Claude Code |