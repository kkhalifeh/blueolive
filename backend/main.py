from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import jwt
import uuid
import json
import logging
import re
from langchain_xai import ChatXAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Initialize LLM
llm = None
if LLM_PROVIDER == "xai" and XAI_API_KEY:
    try:
        llm = ChatXAI(api_key=XAI_API_KEY, model="grok-3")
        logger.info("Initialized xAI ChatXAI (Grok 3)")
    except Exception as e:
        logger.error(f"Failed to initialize xAI ChatXAI: {str(e)}")
elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
    try:
        llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
        logger.info("Initialized OpenAI ChatGPT (GPT-4o)")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI ChatGPT: {str(e)}")
else:
    logger.warning("No valid LLM provider configured. Using rule-based logic.")

# Initialize vector store
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
try:
    vector_store = PGVector(
        connection_string=DATABASE_URL,
        embedding_function=embedding_function,
        collection_name="units",
        distance_strategy="cosine"
    )
    logger.info("Initialized PGVector store")
except Exception as e:
    logger.error(f"Failed to initialize PGVector: {str(e)}")
    vector_store = None

# Pydantic models
class Unit(BaseModel):
    unit_id: int
    project_id: int
    unit_number: str | None
    address: str
    size_sqm: float
    price_jod: float
    bedrooms: int
    bathrooms: int
    floor_type: str | None
    floor_number: int | None
    description_ar: str
    photos_urls: list[str]

class Chat(BaseModel):
    chat_id: int
    conversation_id: str
    user_message: str | None
    bot_response: str | None
    timestamp: datetime

class AISetting(BaseModel):
    setting_id: int
    prompt: str
    temperature: float
    max_tokens: int
    updated_at: datetime
    updated_by: str | None

class Customer(BaseModel):
    name: str | None
    email: str | None
    phone_number: str | None
    preferences: dict | None

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

# JWT authentication
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Placeholder admin login
@app.get("/token")
async def get_token():
    payload = {"sub": "admin"}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# Endpoint to query units
@app.get("/units", response_model=list[Unit])
async def get_units(bedrooms: int | None = None, max_price: float | None = None, location: str | None = None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE 1=1"
        params = []
        if bedrooms:
            query += " AND bedrooms = %s"
            params.append(bedrooms)
        if max_price:
            query += " AND price_jod <= %s"
            params.append(max_price)
        if location:
            query += " AND address ILIKE %s"
            params.append(f"%{location}%")
        cur.execute(query, params)
        units = cur.fetchall()
        cur.close()
        conn.close()
        return units
    except Exception as e:
        logger.error(f"Error fetching units: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching units: {str(e)}")

# Admin endpoint to list units
@app.get("/admin/units", response_model=list[Unit])
async def get_admin_units(token: str = Depends(verify_token)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units")
        units = cur.fetchall()
        cur.close()
        conn.close()
        return units
    except Exception as e:
        logger.error(f"Error fetching admin units: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching admin units: {str(e)}")

# Admin endpoint to list chat history
@app.get("/admin/chats", response_model=list[Chat])
async def get_chats(token: str = Depends(verify_token)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT chat_id, conversation_id, user_message, bot_response, timestamp FROM Chats")
        chats = cur.fetchall()
        cur.close()
        conn.close()
        return chats
    except Exception as e:
        logger.error(f"Error fetching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chats: {str(e)}")

# Admin endpoint to get AI settings
@app.get("/admin/ai-settings", response_model=list[AISetting])
async def get_ai_settings(token: str = Depends(verify_token)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT setting_id, prompt, temperature, max_tokens, updated_at, updated_by FROM AI_Settings")
        settings = cur.fetchall()
        cur.close()
        conn.close()
        return settings
    except Exception as e:
        logger.error(f"Error fetching AI settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching AI settings: {str(e)}")

# Endpoint to create a customer
@app.post("/customers")
async def create_customer(customer: Customer):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        conversation_id = str(uuid.uuid4())
        preferences_json = json.dumps(customer.preferences) if customer.preferences else None
        cur.execute(
            """
            INSERT INTO Customers (conversation_id, name, email, phone_number, preferences)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING customer_id
            """,
            (conversation_id, customer.name, customer.email, customer.phone_number, preferences_json)
        )
        customer_id = cur.fetchone()['customer_id']
        conn.commit()
        cur.close()
        conn.close()
        return {"customer_id": customer_id, "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")

# Chat endpoint
@app.post("/chat")
async def chat(chat_request: ChatRequest):
    try:
        # Get or create conversation_id
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        user_message = chat_request.message

        # Get AI settings
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT prompt, temperature, max_tokens FROM AI_Settings ORDER BY setting_id DESC LIMIT 1")
        ai_settings = cur.fetchone()
        cur.close()

        # Parse preferences
        preferences = {}
        budget_match = re.search(r'(\d+)(?:\s*(?:jod|jd|\$))?', user_message.lower())
        if budget_match:
            preferences["budget"] = float(budget_match.group(1))
        bedrooms_match = re.search(r'(\d+)\s*bedroom', user_message.lower())
        if bedrooms_match:
            preferences["bedrooms"] = int(bedrooms_match.group(1))
        
        # Enhanced location extraction with multi-language support
        location_aliases = {
            "abu alanda": "ابو علندا",
            "abualanda": "ابو علندا", 
            "abu allanda": "ابو علندا",
            "أبو علندا": "ابو علندا",
            "ابو علندا": "ابو علندا",
            "rashid": "ضاحية الرشيد",
            "dahiat rashid": "ضاحية الرشيد",
            "ضاحية الرشيد": "ضاحية الرشيد",
            "mansour": "حي المنصور",
            "hai almansour": "حي المنصور",
            "حي المنصور": "حي المنصور"
        }
        
        for alias, location in location_aliases.items():
            if alias in user_message.lower():
                preferences["location"] = location
                break

        # Get existing preferences first
        cur = conn.cursor()
        cur.execute("SELECT preferences FROM Customers WHERE conversation_id = %s", (conversation_id,))
        customer = cur.fetchone()
        existing_preferences = {}
        if customer and customer['preferences']:
            existing_preferences = customer['preferences']
        
        # Merge preferences if we have new ones
        if preferences:
            merged_preferences = existing_preferences.copy()
            merged_preferences.update(preferences)
            
            logger.info(f"Merging preferences: existing={existing_preferences}, new={preferences}, merged={merged_preferences}")
            
            # Update or create customer preferences
            if customer:
                cur.execute(
                    "UPDATE Customers SET preferences = %s WHERE conversation_id = %s",
                    (json.dumps(merged_preferences), conversation_id)
                )
                logger.info(f"Updated customer preferences for conversation {conversation_id}")
            else:
                cur.execute(
                    "INSERT INTO Customers (conversation_id, preferences) VALUES (%s, %s)",
                    (conversation_id, json.dumps(merged_preferences))
                )
                logger.info(f"Created new customer for conversation {conversation_id}")
            conn.commit()
            existing_preferences = merged_preferences
        
        cur.close()
        
        # Use existing preferences for context and queries
        preferences_context = json.dumps(existing_preferences)
        logger.info(f"Using preferences for query: {existing_preferences}")

        # Query units based on existing preferences (now merged)
        query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE 1=1"
        params = []
        if existing_preferences.get("budget"):
            query += " AND price_jod <= %s"
            params.append(existing_preferences["budget"])
        if existing_preferences.get("bedrooms"):
            query += " AND bedrooms = %s"
            params.append(existing_preferences["bedrooms"])
        if existing_preferences.get("location"):
            query += " AND address ILIKE %s"
            params.append(f"%{existing_preferences['location']}%")
        
        cur = conn.cursor()
        cur.execute(query, params)
        units = cur.fetchall()
        cur.close()

        unit_context = ""
        if units:
            unit_context = "\n".join([f"Unit {unit['unit_number'] or 'N/A'} at {unit['address']}, {unit['size_sqm']} sqm, {unit['price_jod']} JOD, {unit['bedrooms']} bedrooms, Description: {unit['description_ar']}" for unit in units[:3]])
        else:
            unit_context = "No apartments found matching the criteria."

        if llm and ai_settings:
            # LLM-based response with enhanced context
            system_prompt = f"""{ai_settings['prompt']}

Current Customer Preferences: {preferences_context}

Available Units Based on Preferences:
{unit_context}

Instructions:
- If units are available, present them in a clear, organized format with key details
- If no units match, ask for different criteria or suggest alternatives
- Be conversational and helpful
- Use Arabic or English based on the user's language preference
- Include unit numbers, addresses, sizes, prices, and key features
"""
            
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            
            try:
                # Try LLM response first
                response = llm.invoke(prompt_template.format_messages(), temperature=ai_settings['temperature'], max_tokens=ai_settings['max_tokens'])
                bot_response = response.content
                
                # If LLM response is too generic, use rule-based fallback
                if not bot_response or "how can i help" in bot_response.lower():
                    if units:
                        bot_response = f"Found {len(units)} apartments matching your criteria:\n{unit_context}"
                    else:
                        bot_response = "No apartments found matching your criteria. Please provide more details like budget, bedrooms, or location."
                        
            except Exception as e:
                logger.error(f"LLM failed: {str(e)}")
                # Rule-based fallback
                if units:
                    bot_response = f"Found {len(units)} apartments matching your criteria:\n{unit_context}"
                else:
                    bot_response = "No apartments found matching your criteria. Please provide more details like budget, bedrooms, or location."
        else:
            # Rule-based response when no LLM
            if units:
                bot_response = f"Found {len(units)} apartments matching your criteria:\n{unit_context}"
            else:
                bot_response = "No apartments found matching your criteria. Please provide more details like budget, bedrooms, or location."

        # Store chat in database
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Chats (conversation_id, user_message, bot_response)
            VALUES (%s, %s, %s)
            RETURNING chat_id
            """,
            (conversation_id, user_message, bot_response)
        )
        chat_id = cur.fetchone()['chat_id']
        conn.commit()
        cur.close()
        conn.close()

        return {"conversation_id": conversation_id, "bot_response": bot_response}
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
