# Documentation Overview

## Project Documentation Structure
The project contains comprehensive Japanese documentation covering all aspects of the AI manga generation service "Spell".

## Key Documents

### 1. 実施計画書 (Implementation Plan)
- **File**: 01.ハッカソン実施計画書.md
- **Purpose**: Hackathon strategy and timeline
- **Target**: Win grand prize (¥500,000)
- **Timeline**: 2025/8/5 - 9/24
- **Previous experience**: Reached finals but didn't win

### 2. 既存サービス調査 (Existing Service Research)
- **File**: 02.既存サービス調査.md
- **Competitors**: Midjourney, ComicAI (semi-automatic tools)

### 3. 要件定義書 (Requirements Definition)
- **File**: 03.要件定義書.md
- **Service Name**: Spell
- **Core Feature**: 7-phase HITL processing system
- **Processing Time**: Total 97 seconds (can be optimized to 70s with cache)
- **Key Innovation**: Human-in-the-Loop at each phase with natural language feedback

### 4. システム設計書 (System Design)
- **File**: 04.システム設計書.md
- **Architecture**: Monolithic service on Cloud Run
- **Design Philosophy**: HITL-enabled, serverless-first, in-memory processing
- **Data Layer**: Redis single instance, Cloud Storage + CDN, PostgreSQL

### 5. API設計書 (API Design)
- **File**: 05.API設計書.md
- **Protocol**: HTTPS with TLS 1.3
- **Format**: RESTful JSON
- **Auth**: Firebase Authentication
- **Base URL**: https://api.manga-service.com/api/v1

### 6. データベース設計書 (Database Design)
- **File**: 06.データベース設計書.md

### 7. UI/UX設計書 (UI/UX Design)
- **File**: 07.UI_UX設計書.md

### 8. AI設計書 (AI Design)
- **File**: 08.AI設計書.md
- **Core Technology**: Google Gemini Pro + Imagen 4
- **Processing Model**: Human-in-the-loop collaborative
- **Quality Control**: 70% threshold with max 3 retries

### 9. インフラ設計書 (Infrastructure Design)
- **File**: 09.インフラ設計書.md

### 10. セキュリティ設計書 (Security Design)
- **File**: 10.セキュリティ設計書.md

### 11. テスト設計書 (Test Design)
- **File**: 11.テスト設計書.md

### 12. インフラ最適化設計書 (Infrastructure Optimization Design)
- **File**: 12.インフラ最適化設計書.md

## Use Cases
- **Directory**: docs/use-cases/
- Contains service ideas and AI agent/creator use cases