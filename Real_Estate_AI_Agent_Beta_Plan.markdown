# AI Agent Beta Development Plan for Real Estate Company

## Overview
The Beta version of the AI agent will focus on delivering a web-based chatbot and admin web app to pilot the user experience, test AI capabilities (including image handling), and manage units and chat history. The system will use the provided sample of 10 units, integrate with a CRM (Zoho), and leverage a robust database architecture with Retrieval-Augmented Generation (RAG) for accurate querying. The plan avoids Pinecone for cost efficiency, using PostgreSQL with `pgvector` instead, and excludes an MCP server as LangChain and FastAPI suffice for context management. The architecture is designed to scale for future WhatsApp and mobile integration.

## Assessment of Requirements
### Beta Version Requirements
1. **Web App with Chatbot**:
   - Simulate/pilot user experience with a WhatsApp-like UI.
   - Support conversational AI to qualify customers and suggest units from the 10-unit dataset.
   - Handle image display (e.g., unit photos via URLs) and potentially receive user-uploaded images.
   - Built for testing on the 10 units provided in `Cleaned_Real_Estate_Data_Sample.csv`.
2. **Admin Web App**:
   - Manage units (CRUD operations: create, read, update, delete).
   - Access chat history, including session threads.
   - Admin access to view and adjust AI settings (e.g., prompt, temperature).
   - Secure admin authentication.
3. **Database and RAG Architecture**:
   - Robust database to store unit data, customer interactions, and embeddings.
   - Support structured (e.g., price, bedrooms), geospatial (location-based), and semantic (description-based) queries.
   - RAG pipeline for accurate unit suggestions.
4. **Future Scalability**:
   - Architecture to support future WhatsApp integration, web/mobile chatbot expansion, and Zoho CRM integration.

### Data Assessment (Recap)
The provided CSV contains 10 units with fields like `project_name`, `address`, `size_sqm`, `bedrooms`, `price_jod`, `photos_url`, `description`, and `notes`. Key considerations:
- **Geospatial Data**: Missing `latitude` and `longitude`, requiring geocoding.
- **Embeddings**: `embedding_vector` is empty, needing generation for semantic search.
- **Images**: Stored as Facebook URLs, suitable for display but may need cloud storage (e.g., AWS S3) for reliability.
- **Bilingual Support**: Arabic descriptions require English translation for broader accessibility.
- **CRM Integration**: Zoho CRM will store customer leads and interactions, requiring API integration.

### Key Decisions
- **Pinecone**: Excluded for Beta due to small dataset (10 units) and cost considerations. PostgreSQL with `pgvector` is sufficient for vector storage and semantic search.
- **MCP Server**: Not needed, as LangChain handles conversational context and FastAPI manages API orchestration.
- **Zoho CRM Integration**: Included in Beta to store customer data (e.g., name, phone, preferences) and track leads, using Zoho’s API.
- **Image Handling**: Chatbot will display unit photos via URLs and allow user image uploads (stored in AWS S3).
- **Scalability**: Database and backend designed to handle future growth (e.g., more units, WhatsApp integration).

## Phase-by-Phase Development Plan

### Phase 1: Requirements Refinement and Setup (2 Weeks)
- **Objective**: Finalize requirements, set up development environment, and design schemas.
- **Tasks**:
  - Refine chatbot intents: greet, qualify (budget, bedrooms, location), suggest units, display photos, collect contact info, handle image uploads.
  - Design WhatsApp-like UI wireframes for chatbot (e.g., chat bubbles, image previews, buttons).
  - Design admin web app wireframes for unit management, chat history, and AI settings.
  - Finalize database schema (below) and Zoho CRM integration plan.
  - Set up development tools (e.g., Git, AWS account, Zoho API credentials).
- **Deliverables**:
  - Requirements document.
  - UI wireframes for chatbot and admin app.
  - Database schema (SQL DDL).
  - Zoho CRM API setup guide.
- **Team**: Product manager, UI/UX designer, database engineer.

### Phase 2: Database and Backend Development (3 Weeks)
- **Objective**: Build and populate the database, set up backend APIs, and integrate with Zoho CRM.
- **Tasks**:
  - Set up PostgreSQL with PostGIS and `pgvector` on AWS RDS.
  - Migrate CSV data:
    - Geocode addresses using Google Maps API or OpenStreetMap to populate `latitude` and `longitude`.
    - Generate embeddings for `description` and `notes` using `sentence-transformers`.
    - Store photos in AWS S3, updating `photos_urls` with S3 links.
  - Develop FastAPI backend with endpoints:
    - `/units`: Query units (e.g., `?budget=70000&bedrooms=3&location=ابو علندا`).
    - `/units/near`: Geospatial queries (e.g., `?lat=31.95&lon=35.93&radius=5km`).
    - `/customers`: Store customer data (linked to Zoho CRM).
    - `/admin/units`: CRUD operations for units (admin-only).
    - `/admin/chats`: Retrieve chat history.
    - `/admin/ai-settings`: View/update AI prompt and settings (e.g., temperature).
    - `/images/upload`: Handle user image uploads to S3.
  - Integrate Zoho CRM API:
    - Create leads for customers (name, phone, email, preferences).
    - Sync conversation data (e.g., preferences, selected units) to Zoho.
  - Implement JWT-based authentication for admin endpoints.
- **Deliverables**:
  - Populated PostgreSQL database.
  - FastAPI backend with documented APIs.
  - Zoho CRM integration for lead management.
- **Team**: Database engineer, backend developer, API integration specialist.

### Database Schema
**Table: Units**
- `unit_id`: SERIAL PRIMARY KEY
- `project_name`: VARCHAR(50)
- `apartment_number`: VARCHAR(50)
- `address`: TEXT
- `location`: GEOMETRY(POINT, 4326) (PostGIS)
- `size_sqm`: FLOAT
- `bedrooms`: INTEGER
- `bathrooms`: INTEGER
- `floor`: INTEGER
- `price_jod`: FLOAT
- `delivery_status`: VARCHAR(50)
- `description`: TEXT
- `notes`: TEXT
- `photos_urls`: TEXT[] (S3 URLs)
- `video_urls`: TEXT[] (nullable)
- `embedding_vector`: VECTOR (pgvector)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

**Table: Customers**
- `customer_id`: SERIAL PRIMARY KEY
- `conversation_id`: VARCHAR(50)
- `name`: VARCHAR(100) (nullable)
- `email`: VARCHAR(100) (nullable)
- `phone_number`: VARCHAR(20) (nullable)
- `preferences`: JSONB
- `zoho_lead_id`: VARCHAR(50) (links to Zoho CRM)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

**Table: Chats**
- `chat_id`: SERIAL PRIMARY KEY
- `conversation_id`: VARCHAR(50)
- `user_message`: TEXT
- `bot_response`: TEXT
- `timestamp`: TIMESTAMP

**Table: AI_Settings**
- `setting_id`: SERIAL PRIMARY KEY
- `prompt`: TEXT (AI prompt)
- `temperature`: FLOAT (e.g., 0.7)
- `max_tokens`: INTEGER (e.g., 1000)
- `updated_at`: TIMESTAMP
- `updated_by`: VARCHAR(100) (admin user)

### Phase 3: AI Agent Development (3 Weeks)
- **Objective**: Build the RAG-based AI chatbot using LangChain.
- **Tasks**:
  - Set up LangChain with Grok 3 (via xAI API, https://x.ai/api) or GPT-4o.
  - Implement RAG pipeline:
    - Index unit embeddings in `pgvector` for semantic search.
    - Query structured data (price, bedrooms) via SQL and geospatial data via PostGIS.
    - Combine results for accurate unit suggestions.
  - Design conversational flow:
    - Greet: “مرحبا! كيف يمكنني مساعدتك في العثور على شقة؟” (or English equivalent).
    - Qualify: Ask for budget, bedrooms, location, size.
    - Suggest: Retrieve and present up to 3 units with details and photo URLs.
    - Handle images: Display unit photos and store user uploads in S3.
    - Collect contact info and sync with Zoho CRM.
  - Implement bilingual support using DeepL API for Arabic/English translation.
  - Store chat history in `Chats` table, linked to `conversation_id`.
  - Allow admin to adjust AI settings (prompt, temperature) via `/admin/ai-settings` endpoint.
- **Deliverables**:
  - LangChain-based AI agent with RAG.
  - Bilingual conversation support.
  - Image handling (display and upload).
- **Team**: AI developer, NLP engineer.

### Phase 4: Web App (Chatbot) Development (3 Weeks)
- **Objective**: Build a WhatsApp-like chatbot UI for user testing.
- **Tasks**:
  - Develop React app with Tailwind CSS, mimicking WhatsApp UI (chat bubbles, image previews, buttons).
  - Integrate with FastAPI via WebSocket for real-time chat.
  - Display unit details (text, photos) and support image uploads.
  - Add language toggle (Arabic/English).
  - Test responsiveness and accessibility.
- **Deliverables**:
  - Deployed chatbot web app.
- **Team**: Frontend developer, UI/UX designer.

### Phase 5: Admin Web App Development (3 Weeks)
- **Objective**: Build an admin interface for unit management, chat history, and AI settings.
- **Tasks**:
  - Develop React app with Tailwind CSS for admin dashboard.
  - Implement features:
    - Unit management: CRUD operations via `/admin/units` endpoint.
    - Chat history: View sessions/threads via `/admin/chats`.
    - AI settings: View/edit prompt, temperature via `/admin/ai-settings`.
  - Add JWT-based authentication for admin access.
  - Integrate with Zoho CRM to view synced leads.
  - Test usability and security.
- **Deliverables**:
  - Deployed admin web app.
- **Team**: Frontend developer, backend developer.

### Phase 6: Testing and Quality Assurance (2 Weeks)
- **Objective**: Ensure system reliability and accuracy.
- **Tasks**:
  - Test database queries (SQL, geospatial, vector).
  - Test AI agent for conversational accuracy, image handling, and Zoho integration.
  - Test chatbot and admin web apps for usability and responsiveness.
  - Conduct security testing (e.g., JWT, data encryption).
  - Validate bilingual support and image upload/display.
- **Deliverables**:
  - Test reports and bug fixes.
- **Team**: QA engineer, AI developer, backend developer.

### Phase 7: Deployment and Monitoring (1 Week)
- **Objective**: Launch Beta and monitor performance.
- **Tasks**:
  - Deploy FastAPI backend on AWS ECS.
  - Deploy PostgreSQL on AWS RDS.
  - Deploy chatbot and admin web apps on Netlify/Vercel.
  - Set up AWS CloudWatch for backend monitoring.
  - Use Google Analytics for chatbot usage tracking.
  - Configure Sentry for error tracking.
  - Test Zoho CRM sync in production.
- **Deliverables**:
  - Live Beta (chatbot and admin apps).
  - Monitoring dashboards.
- **Team**: DevOps engineer, backend developer.

### Phase 8: Future Scalability Planning (Post-Beta)
- **Objective**: Prepare for WhatsApp, mobile, and full-scale deployment.
- **Tasks**:
  - Plan WhatsApp Business API integration (Phase 5 of original plan).
  - Design mobile app (React Native) or optimize web app for mobile.
  - Enhance Zoho CRM integration (e.g., automated follow-ups).
  - Evaluate Pinecone if dataset grows significantly.
- **Deliverables**:
  - Roadmap for full deployment.
- **Team**: Product manager, developers.

**Total Timeline**: ~17 weeks (4 months) for Beta, assuming a small team.

## Technology Stack
### Database
- **PostgreSQL with PostGIS and pgvector**:
  - Use: Structured, geospatial, and vector storage for units and chats.
  - Hosting: AWS RDS.
- **AWS S3**:
  - Use: Store unit photos and user-uploaded images.

### Backend
- **FastAPI**:
  - Use: REST APIs for unit queries, customer data, admin functions, and image uploads.
- **Python Libraries**:
  - `pandas`: CSV data import.
  - `psycopg2`: PostgreSQL connector.
  - `sentence-transformers`: Generate embeddings.
  - `geopy`: Geocode addresses.
  - `python-jwt`: Admin authentication.

### AI Agent
- **LangChain**:
  - Use: RAG pipeline, conversational memory, and tool integration.
- **LLM**: Grok 3 (xAI API, https://x.ai/api) or GPT-4o.
  - Use: Conversational responses and preference parsing.
- **DeepL API**:
  - Use: Arabic/English translation.

### Frontend (Chatbot and Admin Apps)
- **React with Tailwind CSS**:
  - Use: WhatsApp-like chatbot UI and admin dashboard.
- **WebSocket**:
  - Use: Real-time chat for chatbot app.
- **CDN Libraries**:
  - React, React DOM, Babel, Tailwind CSS.

### CRM Integration
- **Zoho CRM API**:
  - Use: Sync customer data and leads.
  - Setup: Requires Zoho API credentials and OAuth setup.

### Deployment and Monitoring
- **AWS**:
  - ECS: Host FastAPI.
  - RDS: Host PostgreSQL.
  - S3: Store images.
  - CloudWatch: Monitor backend.
- **Netlify/Vercel**:
  - Use: Host chatbot and admin web apps.
- **Sentry**:
  - Use: Error tracking.
- **Google Analytics**:
  - Use: Track chatbot usage.

## Sample AI Prompt
```plaintext
You are a real estate assistant for Blue Olive Real Estate. Communicate in Arabic or English based on user input. Your goal is to qualify customers and suggest apartments from a database. Follow these steps:

1. Greet politely: "مرحبا! كيف يمكنني مساعدتك في العثور على شقة؟" or "Hello! How can I help you find an apartment?"
2. Ask about budget, bedrooms, location, and size.
3. Retrieve up to 3 matching units, showing address, size, price, and photo URLs.
4. Display photos and ask for feedback.
5. If user uploads an image, store it and acknowledge.
6. Collect name, phone, and email for viewings, syncing to Zoho CRM.
7. Be professional, concise, and avoid suggesting non-existent units.
```

## Conclusion
The Beta plan delivers a web-based chatbot with a WhatsApp-like UI, an admin web app for unit and AI management, and a robust PostgreSQL database with RAG for accurate querying. Zoho CRM integration ensures lead tracking, and the architecture supports future WhatsApp and mobile expansion. Excluding Pinecone and MCP keeps costs low and simplifies development, with `pgvector` and LangChain meeting all requirements. Review this plan and confirm next steps (e.g., start Phase 1 or adjust requirements).