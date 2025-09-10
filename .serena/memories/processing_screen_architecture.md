# Processing Screen Architecture Design

## System Overview
Complete redesign of the manga generation processing screen implementing the 7-phase HITL (Human-in-the-Loop) workflow with real-time WebSocket communication, unified state management, and responsive dual-panel UI.

## Architecture Components

### 1. State Management (Zustand Store)
```typescript
interface ProcessingState {
  // Session Management
  sessionId: string | null
  sessionStatus: 'idle' | 'connecting' | 'processing' | 'completed' | 'error'
  
  // 7-Phase System
  phases: PhaseState[]
  currentPhase: number
  overallProgress: number
  
  // Real-time Communication
  wsClient: WebSocketClient | null
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  
  // HITL Feedback
  feedbackRequired: boolean
  feedbackPhase: number | null
  feedbackTimeout: number | null
  
  // UI State
  leftPanelWidth: number
  showLogs: boolean
  showPhaseDetails: boolean
}

interface PhaseState {
  id: number
  name: string
  description: string
  status: 'pending' | 'processing' | 'waiting_feedback' | 'completed' | 'error'
  progress: number
  startTime: Date | null
  endTime: Date | null
  preview: any | null
  logs: LogEntry[]
  feedbackHistory: FeedbackEntry[]
}
```

### 2. WebSocket Communication Layer
```typescript
class ProcessingWebSocketClient extends WebSocketClient {
  // Phase-specific event handlers
  onPhaseStart(phaseId: number, phaseName: string)
  onPhaseProgress(phaseId: number, progress: number, preview?: any)
  onPhaseComplete(phaseId: number, result: any)
  onFeedbackRequest(phaseId: number, preview: any, timeout?: number)
  onFeedbackApplied(phaseId: number, updatedPreview: any)
  
  // HITL Communication
  submitPhaseFeedback(phaseId: number, feedback: string)
  skipPhaseFeedback(phaseId: number, reason: string)
  sendQuickAction(phaseId: number, action: string)
}
```

### 3. Component Architecture
```
ProcessingScreen/
├── ProcessingLayout.tsx           # Main dual-panel container
├── LeftPanel/
│   ├── LogsContainer.tsx         # Real-time log streaming
│   ├── HITLFeedbackInput.tsx     # Feedback input interface
│   └── ConnectionStatus.tsx      # WebSocket status indicator
├── RightPanel/
│   ├── PhaseProgressOverview.tsx # 7-phase progress grid
│   ├── PhaseBlock.tsx           # Individual phase status block
│   └── PhasePreview.tsx         # Phase result preview
├── stores/
│   ├── processingStore.ts       # Main Zustand store
│   └── websocketStore.ts        # WebSocket state management
└── hooks/
    ├── useProcessingSession.ts  # Session lifecycle management
    ├── useWebSocketConnection.ts # WebSocket connection management
    └── useHITLFeedback.ts       # HITL feedback handling
```

### 4. Data Flow Architecture
```
1. Session Initialization:
   User Input → API Call → Session Creation → WebSocket Connection

2. Phase Execution Flow:
   Backend Phase Start → WebSocket Event → Store Update → UI Update

3. HITL Feedback Flow:
   Feedback Request → UI Prompt → User Input → WebSocket Send → Backend Processing

4. Real-time Updates:
   Backend Events → WebSocket → Store Actions → Component Re-renders
```

### 5. Integration Points

#### Backend API Integration:
- `/api/v1/manga/generate` - Session creation
- `/api/v1/manga/{id}/status` - Status polling fallback
- `/api/v1/manga/{id}/feedback` - HITL feedback submission
- `/api/v1/manga/{id}/cancel` - Session cancellation

#### WebSocket Events:
- `session_start` → Initialize phase tracking
- `phase_start` → Update phase status to processing
- `phase_complete` → Mark phase complete, show results
- `feedback_request` → Show HITL input interface
- `preview_ready` → Display phase preview
- `session_complete` → Show final results

### 6. Responsive Design Strategy
```css
/* Mobile-first responsive breakpoints */
@media (max-width: 768px) {
  /* Single column stack layout */
  .processing-container { flex-direction: column; }
  .left-panel { flex: 0 0 60%; }
  .right-panel { flex: 1; }
}

@media (min-width: 769px) {
  /* Dual-panel side-by-side */
  .processing-container { flex-direction: row; }
  .left-panel { flex: 1; min-width: 400px; }
  .right-panel { flex: 0 0 400px; }
}
```

### 7. Error Handling & Recovery
- WebSocket reconnection with exponential backoff
- Phase timeout handling with user notifications
- Graceful degradation to polling if WebSocket fails
- Session recovery on page refresh using sessionId

### 8. Performance Optimizations
- Virtual scrolling for large log streams
- Memoized phase components to prevent unnecessary re-renders
- Debounced feedback input to reduce API calls
- Lazy loading of phase previews

## Implementation Priority
1. Zustand store setup with 7-phase state management
2. WebSocket client integration and event handling
3. Basic dual-panel layout with responsive design
4. HITL feedback interface implementation
5. Real-time log streaming and phase progress
6. Error handling and session recovery
7. Performance optimizations and testing