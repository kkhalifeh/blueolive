-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects table
CREATE TABLE Projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Units table
CREATE TABLE Units (
    unit_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES Projects(project_id),
    unit_number VARCHAR(20),
    address TEXT NOT NULL,
    location GEOMETRY(POINT, 4326),
    size_sqm FLOAT NOT NULL,
    bedrooms INTEGER NOT NULL,
    bathrooms INTEGER NOT NULL,
    floor_type VARCHAR(20),
    floor_number INTEGER,
    price_jod FLOAT NOT NULL,
    delivery_status VARCHAR(50) NOT NULL,
    description_ar TEXT NOT NULL,
    description_en TEXT,
    features JSONB,
    photos_urls TEXT[],
    video_urls TEXT[],
    embedding_vector VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts table
CREATE TABLE Contacts (
    contact_id SERIAL PRIMARY KEY,
    unit_id INTEGER REFERENCES Units(unit_id),
    contact_type VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    phone_number VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE Customers (
    customer_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    email VARCHAR(100),
    phone_number VARCHAR(20),
    preferences JSONB,
    zoho_lead_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chats table
CREATE TABLE Chats (
    chat_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    user_message TEXT,
    bot_response TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI_Settings table
CREATE TABLE AI_Settings (
    setting_id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Create indexes for performance
CREATE INDEX idx_units_location ON Units USING GIST (location);
CREATE INDEX idx_units_price ON Units (price_jod);
CREATE INDEX idx_units_bedrooms ON Units (bedrooms);
CREATE INDEX idx_units_size ON Units (size_sqm);
CREATE INDEX idx_customers_conversation_id ON Customers (conversation_id);
CREATE INDEX idx_chats_conversation_id ON Chats (conversation_id);
