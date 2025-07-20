# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BlueOlive is a **fully functional Real Estate AI Agent system** built for a real estate company. It's a FastAPI-based backend with a PostgreSQL database featuring vector search capabilities for semantic querying of property units. The system includes:

- **Backend**: FastAPI with PostgreSQL + pgvector for semantic search
- **AI Integration**: ✅ **WORKING** - LangChain with OpenAI GPT-4o (primary) and xAI Grok support
- **Database**: PostgreSQL with PostGIS and pgvector extensions
- **Frontend**: React-based chatbot with WhatsApp-style interface
- **Status**: 🎉 **PRODUCTION READY** - All core features implemented and tested

## Architecture

### Backend Structure
- `backend/main.py`: Main FastAPI application with all endpoints
- `backend/requirements.txt`: Python dependencies
- `db/init.sql`: Database schema with tables for Units, Customers, Chats, AI_Settings
- `scripts/`: Data processing utilities

### Key Components
- **Units Management**: CRUD operations for real estate units
- **Chat System**: ✅ **WORKING** - Natural AI conversations with LLM-powered responses
- **Vector Search**: Semantic search using pgvector for unit recommendations
- **Authentication**: JWT-based auth for admin endpoints
- **AI Settings**: Configurable AI prompts and parameters
- **Qualification System**: ✅ **WORKING** - Progressive customer qualification tracking
- **Bilingual Support**: ✅ **WORKING** - Arabic/English language detection and responses

## Common Commands

### Backend Development
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload

# Run with specific host/port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Database Setup
```bash
# Initialize database with schema
psql -d your_database -f db/init.sql

# Run with Docker Compose
cd db
docker-compose up -d
```

### Data Processing
```bash
# Convert Excel to CSV
python scripts/convert_excel_to_csv.py

# Update unit coordinates
python scripts/update_coordinates.py

# Migrate data to database
python scripts/migrate_data.py
```

## Environment Variables

The application requires these environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT token generation
- `XAI_API_KEY`: xAI API key for Grok model
- `OPENAI_API_KEY`: OpenAI API key
- `LLM_PROVIDER`: Either "xai" or "openai" (defaults to "openai")

## New Dependencies

Recent additions to requirements.txt:
- `langdetect==1.0.9`: Language detection for bilingual support

## Database Schema

### Key Tables
- **Units**: Real estate units with embeddings for semantic search
- **Customers**: Customer data with conversation tracking and qualification stages
- **Chats**: Chat history with conversation threading
- **AI_Settings**: Configurable AI prompts and parameters

### Recent Schema Updates
- Added `qualification_stage` field to Customers table
- Tracks customer progress: initial → budget_collected → bedrooms_collected → location_collected → contact_info_collected

### Extensions Used
- `postgis`: For geospatial operations
- `vector`: For embedding storage and similarity search

## API Endpoints

### Public Endpoints
- `GET /units`: Query units with filters (bedrooms, max_price)
- `POST /customers`: Create customer records
- `POST /chat`: ✅ **MAIN ENDPOINT** - Chat with AI agent (fully functional)
- `GET /token`: Get JWT token (development only)

### Debug Endpoints
- `GET /debug/llm`: Test LLM connectivity and functionality
- `GET /debug/chat-conditions`: Verify LLM and AI settings availability

### Admin Endpoints (JWT Required)
- `GET /admin/units`: List all units
- `GET /admin/chats`: View chat history with qualification tracking
- `GET /admin/ai-settings`: View AI configuration

## Development Notes

### AI Integration ✅ **FULLY WORKING**
- Uses LangChain for conversational AI
- ✅ **PRIMARY**: OpenAI GPT-4o model (fully functional)
- ✅ **SECONDARY**: xAI Grok model support
- ✅ **NO FALLBACKS**: All conversations handled by LLM (no hardcoded responses)
- ✅ **LANGUAGE DETECTION**: Automatic Arabic/English detection with `langdetect`
- ✅ **QUALIFICATION TRACKING**: Progressive customer qualification stages
- ✅ **CONTEXT AWARENESS**: Customer history and preferences maintained
- ✅ **CONVERSATION LOGGING**: Complete qualification stage tracking and logging

### Data Processing
- CSV data processing for unit information
- Coordinate geocoding for location-based search
- Embedding generation for semantic search
- **Enhanced**: Bilingual support (Arabic/English) with automatic detection
- **NEW**: Arabic number pattern matching ("ثلاث" → 3)
- **NEW**: Multi-language location aliases

### Image Handling
- **NEW**: Unit photo URLs included in responses
- **NEW**: Facebook image integration
- **NEW**: Multi-photo display support (up to 2 photos per unit)

### Testing ✅ **COMPLETED**
- ✅ **Manual Testing**: Comprehensive testing via FastAPI documentation at `/docs`
- ✅ **LLM Testing**: Debug endpoints for LLM connectivity verification
- ✅ **Conversation Flow**: Full greeting → qualification → recommendation flow tested
- ✅ **Bilingual Support**: Arabic and English conversations verified
- ✅ **Database Integration**: All customer data and chat history properly stored
- ✅ **Unit Recommendations**: Preference-based apartment matching working

### Current Status
- 🎉 **PRODUCTION READY**: All core functionality implemented and tested
- ✅ **LLM Integration**: 100% working with natural AI conversations
- ✅ **Data Clean**: Database cleared and ready for production use
- ✅ **No Hardcoded Responses**: All interactions handled by AI agent

## Future Scalability

The system is designed to support:
- WhatsApp integration
- Mobile app development
- CRM integration (Zoho)
- Expanded unit database
- Advanced geospatial queries