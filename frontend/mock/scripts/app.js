// メインアプリケーション
class MangaGeneratorApp {
    constructor() {
        this.ui = new UIController();
        this.processor = new PhaseProcessor();
        this.isSessionActive = false;
        
        this.initializeApp();
    }

    // アプリケーション初期化
    initializeApp() {
        console.log('🎨 AI漫画生成アプリケーション開始');
        
        // フェーズプロセッサーのイベントリスナー
        this.setupProcessorEvents();
        
        // UIイベントリスナー
        this.setupUIEvents();
        
        // 初期状態設定
        this.ui.showSection('home');
        
        console.log('✅ アプリケーション初期化完了');
    }

    // フェーズプロセッサーイベント設定
    setupProcessorEvents() {
        // セッション開始
        this.processor.addEventListener('sessionStart', (event) => {
            console.log('📝 セッション開始:', event.detail);
            this.isSessionActive = true;
            this.ui.showSection('processing');
        });

        // フェーズ開始
        this.processor.addEventListener('phaseStart', (event) => {
            const { phaseId, phase } = event.detail;
            console.log(`🔄 フェーズ${phaseId}開始: ${phase.name}`);
            
            this.ui.updateStatus(`フェーズ${phaseId}: ${phase.name}`);
            this.ui.updatePhaseBlock(phaseId, 'processing');
            this.ui.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                `フェーズ${phaseId}: ${phase.name}を開始`,
                'phase'
            );
        });

        // フェーズ完了
        this.processor.addEventListener('phaseComplete', (event) => {
            const { phaseId, phase, result } = event.detail;
            console.log(`✅ フェーズ${phaseId}完了:`, result);
            
            this.ui.updatePhaseBlock(phaseId, 'completed', result);
            this.ui.updateProgress(phaseId);
            this.ui.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                `フェーズ${phaseId}: ${phase.name}が完了しました`,
                'complete'
            );
        });

        // フィードバック待機
        this.processor.addEventListener('feedbackWait', (event) => {
            const { phaseId, phase } = event.detail;
            console.log(`⏳ フィードバック待機中: フェーズ${phaseId}`);
            
            this.ui.updateStatus(`フィードバック待機中: ${phase.name}`);
            this.ui.updatePhaseBlock(phaseId, 'active');
            this.ui.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                `フェーズ${phaseId}のプレビューを確認してフィードバックをお願いします`,
                'system'
            );
        });

        // フィードバック適用
        this.processor.addEventListener('feedbackApplied', (event) => {
            const { phase, feedback } = event.detail;
            console.log(`💬 フィードバック適用: フェーズ${phase}`, feedback);
            
            this.ui.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                `ユーザー: ${feedback}`,
                'feedback'
            );
        });

        // フィードバックタイムアウト
        this.processor.addEventListener('feedbackTimeout', (event) => {
            const { phase } = event.detail;
            console.log(`⏰ フィードバックタイムアウト: フェーズ${phase}`);
            
            this.ui.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                `フェーズ${phase}のフィードバック時間が終了しました`,
                'system'
            );
        });

        // フェーズスキップ
        this.processor.addEventListener('phaseSkipped', (event) => {
            const { phase } = event.detail;
            console.log(`⏭️ フェーズスキップ: フェーズ${phase}`);
        });

        // ログ追加
        this.processor.addEventListener('logAdded', (event) => {
            const { timestamp, message, type } = event.detail;
            this.ui.addLogEntry(timestamp, message, type);
        });

        // セッション完了
        this.processor.addEventListener('sessionComplete', (event) => {
            const { results, feedbackHistory, duration, totalFeedbacks } = event.detail;
            console.log('🎉 セッション完了:', event.detail);
            
            this.isSessionActive = false;
            this.ui.updateStatus(`完了 - 所要時間: ${duration}`);
            this.ui.updateProgress(7);
            
            this.ui.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                `🎊 漫画生成が完了しました！総時間: ${duration}, フィードバック: ${totalFeedbacks}回`,
                'complete'
            );

            // 少し待ってから完成モーダル表示
            setTimeout(() => {
                this.ui.showCompletionModal(results);
            }, 1000);
        });

        // セッション停止
        this.processor.addEventListener('sessionStopped', () => {
            console.log('🛑 セッション停止');
            this.isSessionActive = false;
            this.ui.updateStatus('停止済み');
        });
    }

    // UIイベント設定
    setupUIEvents() {
        // 生成開始ボタン
        if (this.ui.elements.generateBtn) {
            this.ui.elements.generateBtn.addEventListener('click', () => {
                this.startGeneration();
            });
        }

        // フィードバック送信
        document.addEventListener('sendFeedback', (event) => {
            const { feedback } = event.detail;
            if (this.isSessionActive) {
                this.processor.applyFeedback(feedback);
            }
        });

        // フェーズスキップ
        document.addEventListener('skipPhase', () => {
            if (this.isSessionActive) {
                this.processor.skipFeedback();
            }
        });

        // ホームリセット
        document.addEventListener('resetToHome', () => {
            this.resetApplication();
        });
    }

    // 生成開始
    async startGeneration() {
        if (this.isSessionActive) {
            console.warn('⚠️ 既にセッションが実行中です');
            return;
        }

        const inputText = this.ui.elements.storyInput?.value?.trim();
        
        // バリデーション
        if (!inputText) {
            alert('物語のテキストを入力してください。');
            return;
        }

        if (inputText.length < 10) {
            alert('物語のテキストが短すぎます。最低10文字以上入力してください。');
            return;
        }

        if (inputText.length > 5000) {
            alert('物語のテキストが長すぎます。5000文字以内にしてください。');
            return;
        }

        try {
            console.log('🚀 生成開始:', { textLength: inputText.length });
            await this.processor.startSession(inputText);
        } catch (error) {
            console.error('❌ 生成エラー:', error);
            alert('生成を開始できませんでした: ' + error.message);
            this.isSessionActive = false;
        }
    }

    // アプリケーションリセット
    resetApplication() {
        if (this.isSessionActive) {
            this.processor.stopSession();
        }
        
        this.isSessionActive = false;
        console.log('🔄 アプリケーションリセット');
    }

    // 現在の状態取得
    getStatus() {
        return {
            isSessionActive: this.isSessionActive,
            currentSection: this.ui.currentSection,
            processorStatus: this.processor.getStatus()
        };
    }

    // デバッグ用メソッド
    async debugStartFromPhase(phaseId, inputText = null) {
        if (this.isSessionActive) {
            console.warn('⚠️ 既にセッションが実行中です');
            return;
        }

        const text = inputText || MockData.getRandomStory();
        
        try {
            console.log(`🔧 デバッグ: フェーズ${phaseId}から開始`);
            this.ui.showSection('processing');
            await this.processor.debugStartFromPhase(phaseId, text);
            this.isSessionActive = true;
        } catch (error) {
            console.error('❌ デバッグ開始エラー:', error);
            alert('デバッグを開始できませんでした: ' + error.message);
        }
    }

    // サンプルストーリー読み込み
    loadSample(type = 'adventure') {
        this.ui.loadSampleStory(type);
        console.log(`📖 サンプルストーリー読み込み: ${type}`);
    }

    // 完成画面にスキップ
    skipToCompletion() {
        if (this.isSessionActive) {
            this.processor.stopSession();
        }

        // 模擬的な完成結果を生成
        const mockResults = {
            results: MockData.generatePhaseResult(7),
            feedbackHistory: [],
            duration: '5分30秒',
            totalFeedbacks: 2
        };

        this.ui.showSection('processing');
        this.ui.updateProgress(7);
        this.ui.updateStatus('完了');

        setTimeout(() => {
            this.ui.showCompletionModal(mockResults.results);
        }, 500);

        console.log('⏩ 完成画面にスキップ');
    }
}

// アプリケーション初期化
let app;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 DOM読み込み完了 - アプリケーション初期化中...');
    
    try {
        app = new MangaGeneratorApp();
        
        // デバッグ用グローバル関数
        window.debugMangaApp = {
            getStatus: () => app.getStatus(),
            loadSample: (type) => app.loadSample(type),
            startFromPhase: (phaseId, inputText) => app.debugStartFromPhase(phaseId, inputText),
            skipToCompletion: () => app.skipToCompletion(),
            resetApp: () => app.resetApplication(),
            
            // 便利なサンプル
            loadAdventure: () => app.loadSample('adventure'),
            loadRomance: () => app.loadSample('romance'),
            loadMystery: () => app.loadSample('mystery'),
            
            // 各フェーズから開始
            startPhase1: () => app.debugStartFromPhase(1),
            startPhase3: () => app.debugStartFromPhase(3),
            startPhase6: () => app.debugStartFromPhase(6)
        };
        
        console.log('✨ アプリケーション準備完了');
        console.log('🔧 デバッグ関数が利用可能:', Object.keys(window.debugMangaApp));
        console.log('');
        console.log('📝 使用例:');
        console.log('  debugMangaApp.loadAdventure() - 冒険サンプル読み込み');
        console.log('  debugMangaApp.startPhase6() - 画像生成フェーズから開始');
        console.log('  debugMangaApp.skipToCompletion() - 完成画面にスキップ');
        console.log('  debugMangaApp.getStatus() - 現在の状態確認');
        
    } catch (error) {
        console.error('❌ アプリケーション初期化エラー:', error);
    }
});

// グローバルエラーハンドリング
window.addEventListener('error', (event) => {
    console.error('🚨 予期しないエラー:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('🚨 未処理のPromise拒否:', event.reason);
});

// エクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MangaGeneratorApp;
}