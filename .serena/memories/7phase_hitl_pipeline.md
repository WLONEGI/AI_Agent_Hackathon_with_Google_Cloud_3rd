# 7-Phase HITL Pipeline Architecture

## Overview
Human-in-the-Loop (HITL) system enabling user feedback at each processing phase for collaborative manga creation.

## Phase Details

### Phase 1: コンセプト・世界観分析 (Concept & Worldview Analysis)
- **Time**: 12 seconds
- **Function**: Analyze input text for concept, theme, genre, target audience, worldview
- **Preview**: Theme visualization, genre, worldview, target audience
- **Feedback**: Theme modification, genre change, worldview adjustment, atmosphere tuning

### Phase 2: キャラクター設定 (Character Design)
- **Time**: 18 seconds  
- **Function**: Character detail settings & simple visual generation (1-2 reference images)
- **Preview**: Character visuals, personality settings, relationship diagrams
- **Feedback**: Add/delete characters, personality changes, visual adjustments, relationship edits

### Phase 3: プロット・ストーリー構成 (Plot & Story Structure)
- **Time**: 15 seconds
- **Function**: Detailed plot and story structure (3-act structure)
- **Preview**: 3-act structure diagram, narrative arc, emotion curve graph
- **Feedback**: Plot changes, pacing adjustments, climax modifications

### Phase 4: ネーム生成 (Name/Layout Generation)
- **Time**: 20 seconds
- **Function**: Panel layout design, scene details, camera angles, staging instructions
- **Preview**: Panel layout, composition preview, staging directions
- **Feedback**: Panel changes, composition adjustments, staging edits, dialogue positioning

### Phase 5: シーン画像生成 (Scene Image Generation)
- **Time**: 25 seconds
- **Function**: Parallel generation of scene images per panel (using Imagen 4)
- **Preview**: Generated image gallery, style confirmation panel
- **Feedback**: Image regeneration, style changes, quality improvements, color adjustments

### Phase 6: セリフ配置 (Dialogue Placement)
- **Time**: 4 seconds
- **Function**: Speech bubble, dialogue, and sound effect placement optimization
- **Preview**: Speech bubble placement, font display, sound effect positioning
- **Feedback**: Dialogue position adjustments, font changes, sound effect add/delete

### Phase 7: 最終統合・品質調整 (Final Integration & Quality)
- **Time**: 3 seconds
- **Function**: Final quality check, integration, output
- **Preview**: Final page preview, overall composition confirmation
- **Feedback**: Final adjustments, format selection, quality settings

## Performance Metrics
- **Total Processing**: 97 seconds
- **Optimized with Cache**: 70 seconds
- **Feedback Wait Time**: Max 30 minutes per phase
- **Quality Threshold**: 70% minimum
- **Retry Limit**: 3 attempts per phase

## Technical Implementation
- **Agent Model**: Each phase is an independent agent
- **Communication**: EventTarget-based feedback system
- **Natural Language**: All feedback processed as natural language
- **State Management**: Phase 1 worldview info accessible to all phases
- **Parallel Processing**: Phase 5 uses parallel image generation