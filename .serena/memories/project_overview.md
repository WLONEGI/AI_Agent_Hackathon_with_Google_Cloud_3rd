# AI漫画生成サービス (AI Manga Generation Service)

## Project Purpose
- **Hackathon Project**: 第3回 AI Agent Hackathon with Google Cloud
- **Main Goal**: Automatically generate manga from text input using AI
- **Target Users**: Amateur writers, content creators, people wanting to convert novels to manga
- **Key Feature**: Complete automation from text to manga in 10-15 minutes

## Core Functionality
- 8-stage AI processing pipeline for manga generation
- Text → [Analysis → Structure → Split → Design → Layout → Image Gen → Placement → Integration] → Manga
- Quality assurance with 70% threshold
- Multi-format output: PDF (print) + WebP (web)

## Performance Targets
- Processing time: 10-15 minutes per work
- Concurrent processing: 50 requests per instance
- Scaling: 1-50 instances
- Availability: 99.9% target

## Development Status
- Initial infrastructure and both frontend/backend implemented
- Recent commits show completed development environment setup
- Main branch with feature branch workflow