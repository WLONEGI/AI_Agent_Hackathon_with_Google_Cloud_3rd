// UI制御クラス
class UIController {
    constructor() {
        this.currentSection = 'home';
        this.elements = this.initializeElements();
        this.bindEvents();
        this.logContainer = null;
        this.currentLogIndex = 0;
    }

    // 要素の初期化
    initializeElements() {
        return {
            // セクション
            homeSection: document.getElementById('home-section'),
            processingSection: document.getElementById('processing-section'),

            // ホーム画面
            storyInput: document.getElementById('story-input'),
            charCount: document.getElementById('char-count'),
            generateBtn: document.getElementById('generate-btn'),

            // 処理画面
            textOutput: document.getElementById('text-output'),
            feedbackInput: document.getElementById('feedback-input'),
            sendFeedback: document.getElementById('send-feedback'),
            skipPhase: document.getElementById('skip-phase'),
            currentStatus: document.getElementById('current-status'),
            progressText: document.getElementById('progress-text'),
            progressFill: document.getElementById('progress-fill'),
            previewBlocks: document.getElementById('preview-blocks'),

            // 完成モーダル
            completionModal: document.getElementById('completion-modal'),
            downloadPdf: document.getElementById('download-pdf'),
            viewResult: document.getElementById('view-result'),
            newGeneration: document.getElementById('new-generation')
        };
    }

    // イベントバインディング
    bindEvents() {
        // 文字数カウンター
        if (this.elements.storyInput) {
            this.elements.storyInput.addEventListener('input', (e) => {
                const count = e.target.value.length;
                this.elements.charCount.textContent = count;
                
                // 文字数に応じてボタンの状態を変更
                if (this.elements.generateBtn) {
                    this.elements.generateBtn.disabled = count < 10 || count > 5000;
                }
                
                // 文字数制限の表示
                if (count > 5000) {
                    this.elements.charCount.style.color = 'var(--danger)';
                } else if (count > 4500) {
                    this.elements.charCount.style.color = 'var(--warning)';
                } else {
                    this.elements.charCount.style.color = 'var(--text-muted)';
                }
            });
        }

        // フィードバック送信
        if (this.elements.sendFeedback) {
            this.elements.sendFeedback.addEventListener('click', () => {
                this.sendUserFeedback();
            });
        }

        // フェーズスキップ
        if (this.elements.skipPhase) {
            this.elements.skipPhase.addEventListener('click', () => {
                this.dispatchEvent('skipPhase');
            });
        }

        // フィードバック入力でEnter送信
        if (this.elements.feedbackInput) {
            this.elements.feedbackInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendUserFeedback();
                }
            });
        }

        // 完成モーダルのボタン
        if (this.elements.newGeneration) {
            this.elements.newGeneration.addEventListener('click', () => {
                this.resetToHome();
            });
        }

        if (this.elements.downloadPdf) {
            this.elements.downloadPdf.addEventListener('click', () => {
                this.simulateDownload();
            });
        }
    }

    // セクション切り替え
    showSection(sectionName) {
        // 全セクションを非表示
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // 指定セクションを表示
        if (sectionName === 'home' && this.elements.homeSection) {
            this.elements.homeSection.classList.add('active');
            this.currentSection = 'home';
        } else if (sectionName === 'processing' && this.elements.processingSection) {
            this.elements.processingSection.classList.add('active');
            this.currentSection = 'processing';
            this.initializeProcessingView();
        }
    }

    // 処理画面の初期化
    initializeProcessingView() {
        this.clearTextOutput();
        this.resetPreviewBlocks();
        this.updateProgress(0);
        this.updateStatus('処理開始中...');
    }

    // テキスト出力クリア
    clearTextOutput() {
        if (this.elements.textOutput) {
            this.elements.textOutput.innerHTML = `
                <div class="log-entry system">
                    <span class="timestamp">00:00:00</span>
                    <span class="message">システム準備完了 - AI漫画生成を開始します</span>
                </div>
            `;
        }
        this.currentLogIndex = 0;
    }

    // ログエントリー追加
    addLogEntry(timestamp, message, type = 'system') {
        if (!this.elements.textOutput) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="timestamp">${timestamp}</span>
            <span class="message">${message}</span>
        `;

        this.elements.textOutput.appendChild(logEntry);
        
        // 自動スクロール
        this.elements.textOutput.scrollTop = this.elements.textOutput.scrollHeight;

        // ログエントリーにフェードインアニメーション
        logEntry.style.opacity = '0';
        logEntry.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            logEntry.style.transition = 'all 0.3s ease';
            logEntry.style.opacity = '1';
            logEntry.style.transform = 'translateY(0)';
        }, 100);
    }

    // ステータス更新
    updateStatus(status) {
        if (this.elements.currentStatus) {
            this.elements.currentStatus.textContent = status;
        }
    }

    // プログレス更新
    updateProgress(phaseNumber) {
        const progress = (phaseNumber / 7) * 100;
        
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${progress}%`;
        }
        
        if (this.elements.progressText) {
            this.elements.progressText.textContent = `${phaseNumber}/7 完了`;
        }
    }

    // プレビューブロックリセット
    resetPreviewBlocks() {
        const blocks = document.querySelectorAll('.phase-block');
        blocks.forEach(block => {
            block.classList.remove('active', 'completed', 'processing');
            
            const status = block.querySelector('.phase-status');
            if (status) {
                status.textContent = '待機中';
            }
            
            const content = block.querySelector('.block-content');
            if (content) {
                content.innerHTML = `
                    <div class="placeholder">
                        <i class="fas fa-clock"></i>
                        <span>処理開始をお待ちください</span>
                    </div>
                `;
            }
        });
    }

    // フェーズブロック更新
    updatePhaseBlock(phaseId, status, content = null) {
        const block = document.querySelector(`[data-phase="${phaseId}"]`);
        if (!block) return;

        // 前の状態をクリア
        block.classList.remove('active', 'completed', 'processing');
        
        // 新しい状態を設定
        if (status === 'processing') {
            block.classList.add('processing');
            this.updateBlockStatus(block, '処理中...');
        } else if (status === 'completed') {
            block.classList.add('completed');
            this.updateBlockStatus(block, '完了');
        } else if (status === 'active') {
            block.classList.add('active');
            this.updateBlockStatus(block, 'フィードバック待機中');
        }

        // コンテンツ更新
        if (content) {
            this.updateBlockContent(block, content);
        }
    }

    // ブロックステータス更新
    updateBlockStatus(block, statusText) {
        const status = block.querySelector('.phase-status');
        if (status) {
            status.textContent = statusText;
        }
    }

    // ブロックコンテンツ更新
    updateBlockContent(block, result) {
        const contentArea = block.querySelector('.block-content');
        if (!contentArea) return;

        const phaseId = parseInt(block.dataset.phase);
        let html = '';

        switch (phaseId) {
            case 1: // テキスト解析
                html = this.generateTextAnalysisContent(result);
                break;
            case 2: // ストーリー構成
                html = this.generateStoryStructureContent(result);
                break;
            case 3: // シーン分割
                html = this.generateSceneDivisionContent(result);
                break;
            case 4: // キャラクター設計
                html = this.generateCharacterDesignContent(result);
                break;
            case 5: // コマ割り設計
                html = this.generatePanelLayoutContent(result);
                break;
            case 6: // 画像生成
                html = this.generateImageGenerationContent(result);
                break;
            case 7: // 最終統合
                html = this.generateFinalIntegrationContent(result);
                break;
            default:
                html = '<div class="placeholder"><span>プレビューデータなし</span></div>';
        }

        contentArea.innerHTML = html;
    }

    // 各フェーズのコンテンツ生成メソッド
    generateTextAnalysisContent(result) {
        return `
            <div class="preview-content">
                <div class="content-grid">
                    <div class="content-item">
                        <h5>キャラクター</h5>
                        <div class="tag-list">
                            ${result.characters?.map(char => `<span class="tag">${char}</span>`).join('') || ''}
                        </div>
                    </div>
                    <div class="content-item">
                        <h5>テーマ</h5>
                        <div class="tag-list">
                            ${result.themes?.map(theme => `<span class="tag">${theme}</span>`).join('') || ''}
                        </div>
                    </div>
                    <div class="content-item">
                        <h5>ジャンル</h5>
                        <p>${result.genre || '未分類'}</p>
                    </div>
                    <div class="content-item">
                        <h5>複雑度</h5>
                        <p>${result.complexity || '不明'}</p>
                    </div>
                </div>
            </div>
        `;
    }

    generateStoryStructureContent(result) {
        return `
            <div class="preview-content">
                <div class="content-item">
                    <h5>3幕構成</h5>
                    <ul>
                        <li><strong>第1幕:</strong> ${result.structure?.act1 || ''}</li>
                        <li><strong>第2幕:</strong> ${result.structure?.act2 || ''}</li>
                        <li><strong>第3幕:</strong> ${result.structure?.act3 || ''}</li>
                    </ul>
                </div>
                <div class="content-item">
                    <h5>転機ポイント</h5>
                    <ul>
                        ${result.turning_points?.map(point => `<li>${point}</li>`).join('') || ''}
                    </ul>
                </div>
            </div>
        `;
    }

    generateSceneDivisionContent(result) {
        return `
            <div class="preview-content">
                <div class="content-item">
                    <h5>シーン構成</h5>
                    <p>総シーン数: ${result.total_scenes || 0}</p>
                    <p>推定ページ数: ${result.estimated_pages || 0}</p>
                </div>
                <div class="content-grid">
                    ${result.scenes?.slice(0, 4).map(scene => `
                        <div class="content-item">
                            <h5>シーン${scene.id}</h5>
                            <p>${scene.description}</p>
                            <p><small>設定: ${scene.setting}</small></p>
                        </div>
                    `).join('') || ''}
                </div>
            </div>
        `;
    }

    generateCharacterDesignContent(result) {
        return `
            <div class="preview-content">
                ${result.character_designs?.map(char => `
                    <div class="content-item">
                        <h5>${char.name}</h5>
                        <p>${char.description}</p>
                        <div class="tag-list">
                            ${char.visual_traits?.map(trait => `<span class="tag">${trait}</span>`).join('') || ''}
                        </div>
                    </div>
                `).join('') || ''}
            </div>
        `;
    }

    generatePanelLayoutContent(result) {
        return `
            <div class="preview-content">
                <div class="content-item">
                    <h5>構成ルール</h5>
                    <p>${result.composition_rules?.balance || ''}</p>
                    <p>${result.composition_rules?.emphasis || ''}</p>
                </div>
                <div class="content-grid">
                    ${result.panel_layouts?.slice(0, 4).map(layout => `
                        <div class="content-item">
                            <h5>ページ${layout.page}</h5>
                            <p>${layout.panels}コマ (${layout.layout_type})</p>
                        </div>
                    `).join('') || ''}
                </div>
            </div>
        `;
    }

    generateImageGenerationContent(result) {
        return `
            <div class="preview-content">
                <div class="content-item">
                    <h5>生成統計</h5>
                    <p>生成画像数: ${result.generated_count || 0}/${result.total_images || 0}</p>
                    <p>品質スコア: ${Math.round((result.quality_score || 0) * 100)}%</p>
                    <p>生成時間: ${result.generation_time || '不明'}</p>
                </div>
                <div class="content-grid">
                    ${result.sample_images?.slice(0, 4).map(img => `
                        <div class="content-item">
                            <h5>シーン${img.scene_id}</h5>
                            <div style="width: 100%; height: 60px; background: var(--bg-tertiary); border-radius: 4px; display: flex; align-items: center; justify-content: center; margin: 8px 0;">
                                <i class="fas fa-image" style="color: var(--text-muted);"></i>
                            </div>
                            <p style="font-size: 0.75rem;">${img.description}</p>
                        </div>
                    `).join('') || ''}
                </div>
            </div>
        `;
    }

    generateFinalIntegrationContent(result) {
        return `
            <div class="preview-content">
                <div class="content-item">
                    <h5>完成統計</h5>
                    <p>最終ページ数: ${result.final_page_count || 0}</p>
                    <p>セリフ数: ${result.dialogs_count || 0}</p>
                    <p>エフェクト数: ${result.effects_count || 0}</p>
                    <p>完成時間: ${result.completion_time || '不明'}</p>
                </div>
                <div class="content-item">
                    <h5>品質メトリクス</h5>
                    <ul>
                        <li>視覚的一貫性: ${Math.round((result.quality_metrics?.visual_consistency || 0) * 100)}%</li>
                        <li>ストーリー流れ: ${Math.round((result.quality_metrics?.story_flow || 0) * 100)}%</li>
                        <li>キャラ一貫性: ${Math.round((result.quality_metrics?.character_consistency || 0) * 100)}%</li>
                    </ul>
                </div>
            </div>
        `;
    }

    // フィードバック送信
    sendUserFeedback() {
        const feedback = this.elements.feedbackInput?.value.trim();
        if (!feedback) return;

        // フィードバックイベント送信
        this.dispatchEvent('sendFeedback', { feedback });

        // 入力欄クリア
        this.elements.feedbackInput.value = '';
    }

    // 完成モーダル表示
    showCompletionModal(results) {
        if (this.elements.completionModal) {
            this.elements.completionModal.classList.add('active');
        }
    }

    // 完成モーダル非表示
    hideCompletionModal() {
        if (this.elements.completionModal) {
            this.elements.completionModal.classList.remove('active');
        }
    }

    // ホーム画面にリセット
    resetToHome() {
        this.hideCompletionModal();
        this.showSection('home');
        
        // フォームリセット
        if (this.elements.storyInput) {
            this.elements.storyInput.value = '';
        }
        if (this.elements.charCount) {
            this.elements.charCount.textContent = '0';
        }
        if (this.elements.generateBtn) {
            this.elements.generateBtn.disabled = true;
        }

        // リセットイベント
        this.dispatchEvent('resetToHome');
    }

    // ダウンロードシミュレーション
    simulateDownload() {
        this.addLogEntry(
            new Date().toLocaleTimeString('ja-JP'),
            'PDFダウンロードを開始しています...',
            'system'
        );

        setTimeout(() => {
            this.addLogEntry(
                new Date().toLocaleTimeString('ja-JP'),
                'PDFダウンロードが完了しました',
                'complete'
            );
        }, 2000);
    }

    // サンプルストーリー読み込み
    loadSampleStory(type = 'adventure') {
        const story = MockData.sampleStories[type];
        if (story && this.elements.storyInput) {
            this.elements.storyInput.value = story;
            
            // 文字数カウンターを更新
            const event = new Event('input');
            this.elements.storyInput.dispatchEvent(event);
        }
    }

    // イベント送信ヘルパー
    dispatchEvent(eventName, data = {}) {
        const event = new CustomEvent(eventName, { detail: data });
        document.dispatchEvent(event);
    }
}

// エクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIController;
}