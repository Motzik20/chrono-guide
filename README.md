# Chrono Guide

**Chrono Guide** is an intelligent task scheduling system that uses AI to extract tasks from various content sources and automatically schedule them into your calendar based on your availability and preferences.

## What It Does

Chrono Guide is designed to solve the problem of task management and scheduling by:

1. **Smart Task Extraction**: Uses AI to automatically extract tasks from:
   - Images (via OCR and visual analysis)
   - PDF documents
   - Text content
   - Handwritten notes

2. **Intelligent Scheduling**: Automatically schedules extracted tasks by:
   - Analyzing your weekly availability patterns
   - Considering task priorities and deadlines
   - Optimizing for time efficiency
   - Splitting large tasks across multiple time slots when needed

3. **Calendar Integration**: Seamlessly integrates with your existing calendar system to avoid conflicts and maintain a unified schedule.

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL)
- **Task Management**: Create, update, and manage tasks with priorities, deadlines, and duration estimates
- **Availability Management**: Set and manage your weekly availability windows
- **Scheduling Engine**: Advanced algorithm that optimally places tasks in available time slots
- **AI Integration**: Google Gemini integration for content analysis and task extraction
- **Calendar Sync**: Integration with external calendar providers

### Key Features
- **Priority-based Scheduling**: Tasks are ranked by deadline urgency, priority level, and duration
- **Task Splitting**: Large tasks can be automatically split across multiple time slots
- **Conflict Resolution**: Intelligent handling of busy periods and availability constraints
- **Multi-week Planning**: Schedule tasks up to 12 weeks in advance
- **Real-time Updates**: Hot-reload development environment with Docker Compose

## 🚀 Getting Started
TODO

## 📋 Current Status

### ✅ Completed
- Database schema with PostgreSQL
- Task and availability models
- Core scheduling algorithm
- Basic API structure
- Comprehensive test suite
- Docker development environment

### 🔄 In Progress
- API endpoint implementation
- AI content processing

### 📅 Planned
- Frontend interface
- Calendar integration
- Advanced scheduling features
- Proper Authentication
- Team collaboration features

## 📄 License

Private project - All rights reserved.

---

**Chrono Guide** - Making task management and scheduling effortless through AI-powered automation.
