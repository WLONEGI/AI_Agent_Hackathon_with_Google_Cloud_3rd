// フェーズ処理エンジン
class PhaseProcessor extends EventTarget {
    constructor() {
        super();
        this.currentPhase = 0;
        this.totalPhases = 7;
        this.isProcessing = false;
        this.sessionData = {
            inputText: '',
            results: {},
            feedbackHistory: [],
            startTime: null,
            endTime: null
        };
        this.processingTimeout = null;
        this.feedbackTimeout = 30000; // 30秒のフィードバックタイムアウト
    }

    // セッション開始
    async startSession(inputText) {
        if (this.isProcessing) {
            throw new Error('既にセッションが実行中です');
        }

        this.sessionData = {
            inputText: inputText,
            results: {},
            feedbackHistory: [],
            startTime: new Date(),
            endTime: null
        };

        this.isProcessing = true;
        this.currentPhase = 1;

        // セッション開始イベント
        this.dispatchEvent(new CustomEvent('sessionStart', {
            detail: { inputText }
        }));

        // 最初のフェーズを開始
        await this.processPhase(1);
    }

    // フェーズ処理
    async processPhase(phaseId) {
        const phase = MockData.phases.find(p => p.id === phaseId);
        if (!phase) {
            throw new Error(`フェーズ${phaseId}が見つかりません`);
        }

        this.currentPhase = phaseId;

        // フェーズ開始イベント
        this.dispatchEvent(new CustomEvent('phaseStart', {
            detail: { phaseId, phase }
        }));

        // ログ出力
        this.addLog(`フェーズ${phaseId}: ${phase.name}を開始しています...`, 'phase');

        // 処理シミュレーション
        this.processingTimeout = setTimeout(async () => {
            const result = MockData.generatePhaseResult(phaseId, this.sessionData.inputText);
            this.sessionData.results[phaseId] = result;

            // フェーズ完了イベント
            this.dispatchEvent(new CustomEvent('phaseComplete', {
                detail: { phaseId, phase, result }
            }));

            this.addLog(`フェーズ${phaseId}: ${phase.name}が完了しました`, 'complete');

            // フィードバック待機開始
            await this.waitForFeedback(phaseId);

        }, phase.duration);
    }

    // フィードバック待機
    async waitForFeedback(phaseId) {
        const phase = MockData.phases.find(p => p.id === phaseId);
        
        // フィードバック待機イベント
        this.dispatchEvent(new CustomEvent('feedbackWait', {
            detail: { 
                phaseId, 
                phase, 
                result: this.sessionData.results[phaseId],
                timeout: this.feedbackTimeout
            }
        }));

        this.addLog(`フェーズ${phaseId}のフィードバックをお待ちしています...`, 'system');

        // フィードバックタイムアウト設定
        this.feedbackTimeout = setTimeout(() => {
            this.handleFeedbackTimeout(phaseId);
        }, 30000);
    }

    // フィードバック適用
    async applyFeedback(feedback) {
        if (!this.isProcessing) {
            throw new Error('フィードバックを適用できる状態ではありません');
        }

        // フィードバックタイムアウトをクリア
        if (this.feedbackTimeout) {
            clearTimeout(this.feedbackTimeout);
            this.feedbackTimeout = null;
        }

        // フィードバック記録
        this.sessionData.feedbackHistory.push({
            phase: this.currentPhase,
            feedback: feedback,
            timestamp: new Date()
        });

        // フィードバック適用イベント
        this.dispatchEvent(new CustomEvent('feedbackApplied', {
            detail: { phase: this.currentPhase, feedback }
        }));

        // AI応答をシミュレート
        const response = MockData.generateFeedbackResponse(feedback);
        this.addLog(`AI: ${response}`, 'feedback');

        // フィードバックに基づく結果修正（簡単なシミュレーション）
        if (feedback && feedback.trim().length > 0) {
            this.addLog('フィードバックを反映して結果を調整中...', 'system');
            
            // 1秒待機してから調整完了
            setTimeout(() => {
                this.addLog('調整が完了しました', 'complete');
                this.proceedToNextPhase();
            }, 1000);
        } else {
            this.proceedToNextPhase();
        }
    }

    // フィードバックスキップ
    async skipFeedback() {
        if (!this.isProcessing) {
            return;
        }

        // フィードバックタイムアウトをクリア
        if (this.feedbackTimeout) {
            clearTimeout(this.feedbackTimeout);
            this.feedbackTimeout = null;
        }

        this.addLog(`フェーズ${this.currentPhase}をスキップしました`, 'system');
        
        // スキップイベント
        this.dispatchEvent(new CustomEvent('phaseSkipped', {
            detail: { phase: this.currentPhase }
        }));

        this.proceedToNextPhase();
    }

    // フィードバックタイムアウト処理
    handleFeedbackTimeout(phaseId) {
        this.addLog(`フェーズ${phaseId}のフィードバック時間が終了しました。自動で次のフェーズに進みます`, 'system');
        
        // タイムアウトイベント
        this.dispatchEvent(new CustomEvent('feedbackTimeout', {
            detail: { phase: phaseId }
        }));

        this.proceedToNextPhase();
    }

    // 次のフェーズに進む
    proceedToNextPhase() {
        if (this.currentPhase >= this.totalPhases) {
            // 全フェーズ完了
            this.completeSession();
            return;
        }

        // 次のフェーズへ
        const nextPhase = this.currentPhase + 1;
        setTimeout(() => {
            this.processPhase(nextPhase);
        }, 1000);
    }

    // セッション完了
    completeSession() {
        this.sessionData.endTime = new Date();
        this.isProcessing = false;

        const duration = this.sessionData.endTime - this.sessionData.startTime;
        const minutes = Math.floor(duration / 60000);
        const seconds = Math.floor((duration % 60000) / 1000);

        this.addLog(`全フェーズが完了しました！総時間: ${minutes}分${seconds}秒`, 'complete');

        // セッション完了イベント
        this.dispatchEvent(new CustomEvent('sessionComplete', {
            detail: {
                results: this.sessionData.results,
                feedbackHistory: this.sessionData.feedbackHistory,
                duration: `${minutes}分${seconds}秒`,
                totalFeedbacks: this.sessionData.feedbackHistory.length
            }
        }));
    }

    // ログ追加
    addLog(message, type = 'system') {
        const timestamp = new Date().toLocaleTimeString('ja-JP', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });

        // ログイベント
        this.dispatchEvent(new CustomEvent('logAdded', {
            detail: {
                timestamp,
                message,
                type
            }
        }));
    }

    // セッション停止
    stopSession() {
        if (this.processingTimeout) {
            clearTimeout(this.processingTimeout);
            this.processingTimeout = null;
        }

        if (this.feedbackTimeout) {
            clearTimeout(this.feedbackTimeout);
            this.feedbackTimeout = null;
        }

        this.isProcessing = false;
        this.currentPhase = 0;

        this.addLog('セッションが停止されました', 'system');

        // セッション停止イベント
        this.dispatchEvent(new CustomEvent('sessionStopped'));
    }

    // 現在の状態取得
    getStatus() {
        return {
            isProcessing: this.isProcessing,
            currentPhase: this.currentPhase,
            totalPhases: this.totalPhases,
            progress: this.currentPhase / this.totalPhases,
            sessionData: { ...this.sessionData }
        };
    }

    // デバッグ用: 特定フェーズから開始
    async debugStartFromPhase(phaseId, inputText = 'デバッグテキスト') {
        if (phaseId < 1 || phaseId > this.totalPhases) {
            throw new Error(`無効なフェーズID: ${phaseId}`);
        }

        // 前のフェーズの結果をモック生成
        for (let i = 1; i < phaseId; i++) {
            this.sessionData.results[i] = MockData.generatePhaseResult(i, inputText);
        }

        this.sessionData.inputText = inputText;
        this.sessionData.startTime = new Date();
        this.isProcessing = true;

        // 指定フェーズを開始
        await this.processPhase(phaseId);
    }
}

// エクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhaseProcessor;
}