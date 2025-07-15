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

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

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
async def get_units(bedrooms: int | None = None, max_price: float | None = None):
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

        # Simple rule-based response
        conn = get_db_connection()
        cur = conn.cursor()
        bot_response = None
        if "budget" in user_message.lower() or "price" in user_message.lower():
            max_price = None
            for word in user_message.split():
                if word.replace(',', '').isdigit():
                    max_price = float(word.replace(',', ''))
                    break
            if max_price:
                query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE price_jod <= %s"
                cur.execute(query, (max_price,))
                units = cur.fetchall()
                if units:
                    bot_response = f"Found {len(units)} apartments within your budget of {max_price} JOD:\n"
                    for unit in units[:3]:
                        bot_response += f"- Unit {unit['unit_number'] or 'N/A'} at {unit['address']}, {unit['size_sqm']} sqm, {unit['price_jod']} JOD\n"
                else:
                    bot_response = "No apartments found within your budget. Try a higher budget or different criteria."
            else:
                bot_response = "Please specify a budget (e.g., 'budget 70000')."
        elif "bedrooms" in user_message.lower():
            bedrooms = None
            for word in user_message.split():
                if word.isdigit():
                    bedrooms = int(word)
                    break
            if bedrooms:
                query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE bedrooms = %s"
                cur.execute(query, (bedrooms,))
                units = cur.fetchall()
                if units:
                    bot_response = f"Found {len(units)} apartments with {bedrooms} bedrooms:\n"
                    for unit in units[:3]:
                        bot_response += f"- Unit {unit['unit_number'] or 'N/A'} at {unit['address']}, {unit['size_sqm']} sqm, {unit['price_jod']} JOD\n"
                else:
                    bot_response = f"No apartments found with {bedrooms} bedrooms."
            else:
                bot_response = "Please specify the number of bedrooms (e.g., '3 bedrooms')."
        else:
            bot_response = "Hello! How can I help you find an apartment? Please specify your budget, number of bedrooms, or location."

        # Store chat in database
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
