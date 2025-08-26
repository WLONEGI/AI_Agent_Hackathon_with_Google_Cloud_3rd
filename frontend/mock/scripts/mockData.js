// モックデータとフェーズ定義
class MockData {
    static phases = [
        {
            id: 1,
            name: 'テキスト解析',
            icon: 'fas fa-search',
            description: 'テキストを分析し、キャラクター、テーマ、感情を抽出します',
            duration: 3000 // 3秒
        },
        {
            id: 2,
            name: 'ストーリー構成',
            icon: 'fas fa-sitemap',
            description: '3幕構成でストーリーの構造を設計します',
            duration: 4000 // 4秒
        },
        {
            id: 3,
            name: 'シーン分割',
            icon: 'fas fa-film',
            description: '物語を漫画のシーンに分割します',
            duration: 3500 // 3.5秒
        },
        {
            id: 4,
            name: 'キャラクター設計',
            icon: 'fas fa-user-friends',
            description: 'キャラクターの外見と関係性を設計します',
            duration: 5000 // 5秒
        },
        {
            id: 5,
            name: 'コマ割り設計',
            icon: 'fas fa-th-large',
            description: 'ページレイアウトとコマ割りを設計します',
            duration: 4500 // 4.5秒
        },
        {
            id: 6,
            name: '画像生成',
            icon: 'fas fa-image',
            description: 'AIが各シーンの画像を生成します',
            duration: 6000 // 6秒
        },
        {
            id: 7,
            name: '最終統合',
            icon: 'fas fa-check-circle',
            description: 'セリフ配置と最終調整を行います',
            duration: 3000 // 3秒
        }
    ];

    // サンプル物語データ
    static sampleStories = {
        adventure: `昔々、緑豊かな森の奥深くにエルフの村がありました。そこに住む若いエルフの戦士エリアは、村を守るため日々修行に励んでいました。

ある日、村に暗黒の魔法使いが現れ、「7日以内に村の宝である光の石を差し出さなければ、村を闇に包む」と脅迫してきました。

エリアは仲間のマージ（魔法使い）とドワーフの戦士ギムリと共に、魔法使いを倒すための冒険に出発しました。彼らは危険な山を越え、古い遺跡で伝説の武器を見つけ、最終的に魔法使いの城へ向かいます。

激しい戦いの末、友情と勇気の力で魔法使いを倒し、村に平和を取り戻しました。エリアは村の英雄となり、新しい冒険への準備を始めるのでした。`,

        romance: `都市の忙しい生活に疲れた会社員の美咲は、故郷の小さな町に帰省することにしました。そこで偶然、幼なじみの健太と再会します。

健太は今、町で小さなカフェを営んでいました。二人は昔のことを思い出しながら、ゆっくりと時間を過ごします。美咲は健太の作るコーヒーと、変わらない優しさに心を癒されていきます。

しかし、美咲には東京に戻らなければならない事情がありました。お互いの気持ちに気づきながらも、なかなか素直になれない二人。

町の夏祭りの夜、花火の下で美咲は自分の本当の気持ちを健太に伝えます。健太も同じ気持ちだったことを告白し、二人は新しい人生を一緒に歩んでいくことを決めるのでした。`,

        mystery: `深夜の雨音が響く中、私立探偵の田中は一本の奇妙な電話を受けた。依頼人は声を震わせながら「誰かが私を見張っている」と告白した。

翌日、指定された喫茶店で待っていたのは上品な身なりの女性・山田さんだった。彼女は最近引っ越した古いマンションで、毎夜同じ時刻に誰かの足音を聞くのだという。

田中は現場調査を開始した。マンションの管理人、近隣住民への聞き込み、そして深夜の張り込み。やがて明らかになったのは、50年前にこのマンションで起きた未解決事件だった。

真相は意外な場所に隠されていた。山田さん自身が無意識に封印していた記憶の中に、すべての答えがあったのだ。`
    };

    // フェーズ結果生成
    static generatePhaseResult(phaseId, inputText = '') {
        const phase = this.phases.find(p => p.id === phaseId);
        if (!phase) return null;

        switch (phaseId) {
            case 1: // テキスト解析
                return {
                    characters: this.extractCharacters(inputText),
                    themes: this.extractThemes(inputText),
                    emotions: this.extractEmotions(inputText),
                    wordCount: inputText.length,
                    complexity: this.calculateComplexity(inputText),
                    genre: this.detectGenre(inputText)
                };

            case 2: // ストーリー構成
                return {
                    structure: {
                        act1: '導入部 - 主人公と世界観の紹介',
                        act2: '展開部 - 問題の発生と困難への挑戦',
                        act3: '結末部 - 解決と成長の物語'
                    },
                    pacing: {
                        slow_scenes: ['日常シーン', '心境描写'],
                        fast_scenes: ['戦闘シーン', 'クライマックス']
                    },
                    turning_points: [
                        '事件の発生',
                        '最初の挫折',
                        '仲間との出会い',
                        '最終決戦'
                    ]
                };

            case 3: // シーン分割
                return {
                    scenes: this.generateScenes(inputText),
                    total_scenes: 8,
                    estimated_pages: 8,
                    scene_types: ['日常', 'アクション', '感情', 'クライマックス']
                };

            case 4: // キャラクター設計
                return {
                    character_designs: [
                        {
                            name: '主人公',
                            description: '勇敢で正義感の強い青年',
                            visual_traits: ['黒髪', '青い瞳', '中背', '凛々しい表情'],
                            personality: ['勇敢', '優しい', '責任感が強い']
                        },
                        {
                            name: '仲間',
                            description: '主人公を支える信頼できる友',
                            visual_traits: ['茶髪', '緑の瞳', '小柄', '明るい笑顔'],
                            personality: ['明るい', '忠実', '機転が利く']
                        }
                    ],
                    style_consistency: {
                        art_style: '少年漫画風',
                        color_palette: ['青', '赤', '金', '白'],
                        visual_themes: ['冒険', '友情', '成長']
                    }
                };

            case 5: // コマ割り設計
                return {
                    panel_layouts: this.generatePanelLayouts(),
                    reading_flow: '縦読み・右から左',
                    composition_rules: {
                        balance: '黄金比を使用した構図',
                        emphasis: '重要シーンは大きなコマで表現',
                        rhythm: 'アクションは小刻みなコマ、感情は大きなコマ'
                    }
                };

            case 6: // 画像生成
                return {
                    sample_images: this.generateSampleImages(),
                    total_images: 24,
                    generated_count: 24,
                    style_applied: '少年漫画スタイル',
                    quality_score: 0.92,
                    generation_time: '4分32秒'
                };

            case 7: // 最終統合
                return {
                    manga_pages: this.generateMangaPages(),
                    dialogs_count: 45,
                    effects_count: 12,
                    final_page_count: 8,
                    completion_time: '28分15秒',
                    quality_metrics: {
                        visual_consistency: 0.95,
                        story_flow: 0.88,
                        character_consistency: 0.92
                    }
                };

            default:
                return {};
        }
    }

    // ヘルパーメソッド
    static extractCharacters(text) {
        const commonNames = ['エリア', 'マージ', 'ギムリ', '美咲', '健太', '田中', '主人公', '仲間'];
        return commonNames.filter(() => Math.random() > 0.5).slice(0, 3);
    }

    static extractThemes(text) {
        const themes = ['冒険', '友情', '成長', '愛', '勇気', '正義', '家族', '絆'];
        return themes.filter(() => Math.random() > 0.6).slice(0, 3);
    }

    static extractEmotions(text) {
        const emotions = ['希望', '緊張', '喜び', '悲しみ', '興奮', '不安', '感動'];
        return emotions.filter(() => Math.random() > 0.6).slice(0, 3);
    }

    static calculateComplexity(text) {
        return text.length < 500 ? '低' : text.length < 1500 ? '中' : '高';
    }

    static detectGenre(text) {
        if (text.includes('魔法') || text.includes('エルフ')) return 'ファンタジー';
        if (text.includes('恋') || text.includes('愛')) return 'ロマンス';
        if (text.includes('事件') || text.includes('謎')) return 'ミステリー';
        return '一般';
    }

    static generateScenes(text) {
        const sceneCount = Math.min(8, Math.max(4, Math.floor(text.length / 100)));
        const scenes = [];
        
        for (let i = 1; i <= sceneCount; i++) {
            scenes.push({
                id: i,
                title: `シーン${i}`,
                description: `物語の第${i}部分`,
                setting: i === 1 ? '導入' : i === sceneCount ? 'クライマックス' : '展開',
                characters: this.extractCharacters(text).slice(0, 2),
                estimated_panels: Math.floor(Math.random() * 4) + 2
            });
        }
        
        return scenes;
    }

    static generatePanelLayouts() {
        const layouts = [];
        for (let page = 1; page <= 8; page++) {
            layouts.push({
                page: page,
                panels: Math.floor(Math.random() * 4) + 3,
                layout_type: ['標準', '縦長', '横長', '変形'][Math.floor(Math.random() * 4)],
                reading_flow: 'Z字型',
                special_effects: page === 4 || page === 8 ? ['見開き', 'インパクト'] : []
            });
        }
        return layouts;
    }

    static generateSampleImages() {
        const images = [];
        for (let i = 1; i <= 6; i++) {
            images.push({
                scene_id: i,
                image_url: `https://via.placeholder.com/400x300/2d2d2d/ffffff?text=Scene+${i}`,
                description: `シーン${i}のプレビュー画像`,
                style: '少年漫画',
                quality: Math.random() * 0.3 + 0.7
            });
        }
        return images;
    }

    static generateMangaPages() {
        const pages = [];
        for (let page = 1; page <= 8; page++) {
            pages.push({
                page: page,
                image_url: `https://via.placeholder.com/400x600/2d2d2d/ffffff?text=Page+${page}`,
                panels: Math.floor(Math.random() * 4) + 3,
                dialogs: [
                    `ページ${page}のセリフ1`,
                    `ページ${page}のセリフ2`
                ],
                effects: ['効果音', '背景効果']
            });
        }
        return pages;
    }

    // ランダムなフィードバック応答を生成
    static generateFeedbackResponse(feedback) {
        const responses = [
            'フィードバックを確認しました。調整を行います。',
            'ご指摘の通りです。修正いたします。',
            'なるほど、そのアプローチも良いですね。適用します。',
            'フィードバックを反映して改善しました。',
            '素晴らしいアイデアです！取り入れさせていただきます。'
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }

    // デバッグ用のクイックアクセス
    static getRandomStory() {
        const stories = Object.values(this.sampleStories);
        return stories[Math.floor(Math.random() * stories.length)];
    }
}

// エクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MockData;
}