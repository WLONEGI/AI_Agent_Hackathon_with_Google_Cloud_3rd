# フェーズ構成比較レポート

## 設計書と実装の比較

### AI設計書（08.AI設計書.md）の定義

#### 7-Phase HITL Pipeline
```
Phase1: プロット生成Agent - 3秒
Phase2: ネーム生成Agent - 7秒  
Phase3: キャラクター詳細設計Agent - 4秒
Phase4: 下書き生成Agent - 4秒
Phase5: 画像生成・ペン入れAgent - 6秒
Phase6: 仕上げ処理Agent - 3秒
Phase7: セリフ配置・最終統合Agent - 3秒
```

#### 8段階AIモジュール（統合サービス内）
```python
'text_analysis': TextAnalysisModule(),          # テキスト解析
'story_structure': StoryStructureModule(),      # ストーリー構成
'scene_division': SceneDivisionModule(),        # シーン分割
'character_design': CharacterDesignModule(),    # キャラクター設計
'panel_layout': PanelLayoutModule(),            # パネルレイアウト
'image_generation': ImageGenerationModule(),    # 画像生成
'dialog_placement': DialogPlacementModule(),    # セリフ配置
'final_integration': FinalIntegrationModule()   # 最終統合
```

### フロントエンド実装（processing.ts）の定義

```typescript
1: {
  name: 'テキスト解析',
  description: 'キャラクター、テーマ、ジャンルの抽出',
  estimatedTime: 3000,
},
2: {
  name: 'ストーリー構成',
  description: '3幕構成での物語構造設計',
  estimatedTime: 4000,
},
3: {
  name: 'シーン分割',
  description: '漫画シーンへの分割と流れ設計',
  estimatedTime: 3500,
},
4: {
  name: 'キャラクター設計',
  description: 'ビジュアルと関係性の詳細設計',
  estimatedTime: 5000,
},
5: {
  name: 'コマ割り設計',
  description: 'レイアウトと読み流しの最適化',
  estimatedTime: 4500,
},
6: {
  name: '画像生成',
  description: 'AI画像生成と調整',
  estimatedTime: 6000,
},
7: {
  name: '最終統合',
  description: 'セリフ配置と最終調整',
  estimatedTime: 3000,
}
```

## 相違点の分析

### 1. フェーズ数の不一致
- **設計書（7-Phase HITL）**: 7フェーズ
- **設計書（8段階モジュール）**: 8モジュール
- **フロントエンド実装**: 7フェーズ

### 2. フェーズ名称と内容の相違

| フェーズ | 設計書（7-Phase） | 設計書（8段階） | フロント実装 |
|---------|------------------|----------------|-------------|
| 1 | プロット生成 | text_analysis | テキスト解析 ✅ |
| 2 | ネーム生成 | story_structure | ストーリー構成 ⚠️ |
| 3 | キャラクター詳細設計 | scene_division | シーン分割 ⚠️ |
| 4 | 下書き生成 | character_design | キャラクター設計 ⚠️ |
| 5 | 画像生成・ペン入れ | panel_layout | コマ割り設計 ⚠️ |
| 6 | 仕上げ処理 | image_generation | 画像生成 ⚠️ |
| 7 | セリフ配置・最終統合 | dialog_placement | 最終統合 ✅ |
| 8 | - | final_integration | - |

### 3. 順序の相違
- **設計書（7-Phase）**: プロット → ネーム → キャラクター → 下書き → 画像 → 仕上げ → セリフ
- **フロント実装**: テキスト解析 → ストーリー構成 → シーン分割 → キャラクター設計 → コマ割り → 画像生成 → 最終統合

### 4. 処理時間の相違

| フェーズ | 設計書時間 | 実装時間 | 差異 |
|---------|-----------|---------|------|
| 1 | 3秒 | 3000ms | ✅ 一致 |
| 2 | 7秒 | 4000ms | ❌ -3秒 |
| 3 | 4秒 | 3500ms | ❌ -0.5秒 |
| 4 | 4秒 | 5000ms | ❌ +1秒 |
| 5 | 6秒 | 4500ms | ❌ -1.5秒 |
| 6 | 3秒 | 6000ms | ❌ +3秒 |
| 7 | 3秒 | 3000ms | ✅ 一致 |

## 推奨される修正方針

### 方針1: フロントエンド実装を設計書に合わせる
**メリット**
- 設計書との完全な一致
- ドキュメントの整合性

**デメリット**
- 現在の実装が論理的により適切な可能性
- 大規模な変更が必要

### 方針2: 設計書を実装に合わせて更新（推奨）
**メリット**
- 現在の実装が論理的な流れに沿っている
- 変更コストが低い
- 8段階モジュールとの対応も明確

**デメリット**
- 設計書の更新が必要

### 方針3: 中間案として名称のみ調整
実装の順序は維持しつつ、名称を調整して設計書との整合性を高める

## 結論

現在のフロントエンド実装は、8段階AIモジュールの構成により近く、論理的な流れになっています：
1. テキスト解析（入力理解）
2. ストーリー構成（物語構造化）
3. シーン分割（場面設計）
4. キャラクター設計（ビジュアル設計）
5. コマ割り設計（レイアウト）
6. 画像生成（ビジュアル生成）
7. 最終統合（セリフ・仕上げ）

この流れは「理解→構造化→詳細化→生成→統合」という自然な処理フローに沿っており、維持することを推奨します。