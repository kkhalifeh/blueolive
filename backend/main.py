from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
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
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
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
app = FastAPI(
    title="BlueOlive Real Estate AI Agent API",
    description="AI-powered real estate chatbot API with bilingual support",
    version="1.0.0"
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend development server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",  # Alternative Vite port
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

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
logger.info(f"LLM_PROVIDER: {LLM_PROVIDER}")
logger.info(f"XAI_API_KEY present: {bool(XAI_API_KEY)}")
logger.info(f"OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")

if LLM_PROVIDER == "xai" and XAI_API_KEY:
    try:
        llm = ChatXAI(api_key=XAI_API_KEY, model="grok-3")
        logger.info("✅ Successfully initialized xAI ChatXAI (Grok 3)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize xAI ChatXAI: {str(e)}")
elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
    try:
        llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
        logger.info("✅ Successfully initialized OpenAI ChatGPT (GPT-4o)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI ChatGPT: {str(e)}")
else:
    logger.warning(f"❌ No valid LLM provider configured. LLM_PROVIDER='{LLM_PROVIDER}', XAI_KEY={bool(XAI_API_KEY)}, OPENAI_KEY={bool(OPENAI_API_KEY)}")

logger.info(f"Final LLM status: {llm is not None}")
if llm:
    logger.info("🎉 LLM is ready for conversations!")
else:
    logger.error("💥 LLM failed to initialize - will use fallback responses")

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

# Language detection function
def detect_language(text: str) -> str:
    """Detect if text is Arabic (ar) or English (en). Default to English."""
    try:
        detected = detect(text)
        if detected == 'ar':
            return 'ar'
        else:
            return 'en'
    except LangDetectException:
        # Default to English if detection fails
        return 'en'

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

# Root endpoint
@app.get("/")
async def read_root():
    return {
        "message": "BlueOlive Real Estate AI Agent API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "chat": "/chat",
            "units": "/units",
            "admin": "/admin/*"
        }
    }

# Placeholder admin login
@app.get("/token")
async def get_token():
    payload = {"sub": "admin"}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# Debug endpoint to test LLM directly
@app.get("/debug/llm")
async def debug_llm():
    logger.info("🔧 LLM Debug endpoint called")
    
    result = {
        "llm_initialized": llm is not None,
        "llm_provider": LLM_PROVIDER,
        "openai_key_present": bool(OPENAI_API_KEY),
        "xai_key_present": bool(XAI_API_KEY)
    }
    
    if llm:
        try:
            from langchain_core.messages import HumanMessage
            test_response = llm.invoke([HumanMessage(content="Say hello")])
            result["llm_test"] = "SUCCESS"
            result["test_response"] = test_response.content
            logger.info("✅ LLM test successful")
        except Exception as e:
            result["llm_test"] = "FAILED" 
            result["error"] = str(e)
            logger.error(f"❌ LLM test failed: {str(e)}")
    else:
        result["llm_test"] = "NOT_INITIALIZED"
        logger.error("❌ LLM not initialized")
    
    return result

# Debug endpoint to check chat conditions
@app.get("/debug/chat-conditions")
async def debug_chat_conditions():
    logger.info("🔧 Chat conditions debug endpoint called")
    
    # Get AI settings just like in chat endpoint
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT prompt, temperature, max_tokens FROM AI_Settings ORDER BY setting_id DESC LIMIT 1")
    ai_settings = cur.fetchone()
    cur.close()
    conn.close()
    
    result = {
        "llm_available": llm is not None,
        "ai_settings_available": ai_settings is not None,
        "condition_check": (llm is not None) and (ai_settings is not None),
        "ai_settings_data": dict(ai_settings) if ai_settings else None
    }
    
    logger.info(f"🔍 Debug result: {result}")
    return result

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
        
        # Detect language
        detected_language = detect_language(user_message)
        logger.info(f"Detected language: {detected_language} for message: {user_message}")

        # Get AI settings
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT prompt, temperature, max_tokens FROM AI_Settings ORDER BY setting_id DESC LIMIT 1")
        ai_settings = cur.fetchone()
        cur.close()

        # Check for pagination requests
        pagination_keywords = ['show more', 'more units', 'see more', 'other options', 'more apartments', 'what else', 'more options', 'اريد المزيد', 'المزيد من الوحدات', 'خيارات أخرى']
        is_pagination_request = any(keyword in user_message.lower() for keyword in pagination_keywords)
        
        # Parse preferences
        preferences = {}
        
        # Check for specific unit number search
        unit_number_patterns = [
            r'unit\s*(\d+)',           # English: unit 117
            r'شقة\s*رقم\s*(\d+)',       # Arabic: شقة رقم 117
            r'وحدة\s*(\d+)',           # Arabic: وحدة 117
            r'about\s*unit\s*(\d+)',   # English: about unit 117
            r'معلومات\s*عن\s*شقة\s*(\d+)', # Arabic: معلومات عن شقة 117
            r'تفاصيل\s*شقة\s*(\d+)',    # Arabic: تفاصيل شقة 113
            r'اعطيني\s*تفاصيل\s*شقة\s*(\d+)', # Arabic: اعطيني تفاصيل شقة 113
            r'شقة\s*(\d+)',            # Arabic: شقة 113  
            r'احكيلي\s*عن\s*شقة\s*(\d+)', # Arabic: احكيلي عن شقة 113
            r'معلومات\s*شقة\s*(\d+)',   # Arabic: معلومات شقة 113
        ]
        
        unit_search = None
        for pattern in unit_number_patterns:
            unit_match = re.search(pattern, user_message.lower())
            if unit_match:
                unit_search = unit_match.group(1)
                logger.info(f"Detected unit number search for: {unit_search}")
                break
        
        # Check for feature-based search (for vector search)
        feature_keywords = [
            'balcony', 'بلكونة', 'بلكونتين', 'garage', 'كراج', 'parking', 'موقف',
            'elevator', 'مصعد', 'garden', 'حديقة', 'view', 'إطلالة', 'مطل',
            'furnished', 'مفروش', 'kitchen', 'مطبخ', 'terrace', 'تراس'
        ]
        
        has_feature_search = any(keyword in user_message.lower() for keyword in feature_keywords)
        logger.info(f"Feature search detection: {has_feature_search} for message: {user_message}")
        logger.info(f"Vector store available: {vector_store is not None}")
        
        # Budget extraction - more specific patterns to avoid conflict with bedroom numbers
        budget_patterns = [
            r'بميزانية\s*(\d+)',  # Arabic: بميزانية 60000
            r'ميزانية\s*(\d+)',   # Arabic: ميزانية 60000
            r'budget\s*(\d+)',    # English: budget 60000
            r'(\d{4,})\s*(?:jod|jd)', # 4+ digits followed by JOD
            r'(\d{4,})\s*دينار',  # 4+ digits followed by دينار
            r'(\d{4,})\s*(?:$|dollar)', # 4+ digits followed by $ or dollar
        ]
        
        budget_match = None
        for pattern in budget_patterns:
            budget_match = re.search(pattern, user_message.lower())
            if budget_match:
                preferences["budget"] = float(budget_match.group(1))
                logger.info(f"Extracted budget: {preferences['budget']} from pattern: {pattern}")
                break
        # English pattern
        bedrooms_match = re.search(r'(\d+)\s*bedrooms?', user_message.lower())
        if not bedrooms_match:
            # Arabic patterns - enhanced to catch more variations
            arabic_digit_pattern = re.search(r'(\d+)\s*غرف?', user_message)
            arabic_word_pattern = re.search(r'(ثلاث|اثنين|واحد|أربع|خمس)\s*غرف?', user_message)
            
            if arabic_digit_pattern:
                preferences["bedrooms"] = int(arabic_digit_pattern.group(1))
                logger.info(f"Extracted Arabic bedrooms (digit): {arabic_digit_pattern.group(1)}")
            elif arabic_word_pattern:
                arabic_numbers = {'واحد': 1, 'اثنين': 2, 'ثلاث': 3, 'أربع': 4, 'خمس': 5}
                bedroom_text = arabic_word_pattern.group(1)
                preferences["bedrooms"] = arabic_numbers[bedroom_text]
                logger.info(f"Extracted Arabic bedrooms (word): {bedroom_text} -> {arabic_numbers[bedroom_text]}")
        elif bedrooms_match:
            preferences["bedrooms"] = int(bedrooms_match.group(1))
            
        if preferences.get("bedrooms"):
            logger.info(f"Extracted bedrooms: {preferences['bedrooms']}")
        
        logger.info(f"Extracted preferences from message '{user_message}': {preferences}")
        logger.info(f"Is pagination request: {is_pagination_request}")
        
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

        # Get existing preferences and qualification stage
        cur = conn.cursor()
        cur.execute("SELECT preferences, qualification_stage FROM Customers WHERE conversation_id = %s", (conversation_id,))
        customer = cur.fetchone()
        existing_preferences = {}
        current_stage = 'initial'
        if customer:
            if customer['preferences']:
                existing_preferences = customer['preferences']
            current_stage = customer.get('qualification_stage', 'initial')
        
        # Always update language preference and merge other preferences
        merged_preferences = existing_preferences.copy()
        merged_preferences["language"] = detected_language
        
        # Initialize units_shown if not exists
        if "units_shown" not in merged_preferences:
            merged_preferences["units_shown"] = []
        
        # If new preferences are provided (not just pagination), reset units_shown
        if preferences and not is_pagination_request:
            merged_preferences.update(preferences)
            merged_preferences["units_shown"] = []  # Reset pagination on new search
            logger.info(f"New search: Merging preferences: existing={existing_preferences}, new={preferences}, merged={merged_preferences}")
        elif is_pagination_request:
            logger.info(f"Pagination request detected, keeping existing units_shown: {merged_preferences.get('units_shown', [])}")
        
        # Determine qualification stage based on collected preferences
        new_stage = current_stage
        if merged_preferences.get("budget") and current_stage == 'initial':
            new_stage = 'budget_collected'
        elif merged_preferences.get("bedrooms") and current_stage in ['initial', 'budget_collected']:
            new_stage = 'bedrooms_collected'
        elif merged_preferences.get("location") and current_stage in ['initial', 'budget_collected', 'bedrooms_collected']:
            new_stage = 'location_collected'
        elif merged_preferences.get("name") or merged_preferences.get("phone") or merged_preferences.get("email"):
            new_stage = 'contact_info_collected'
        
        logger.info(f"Qualification stage: {current_stage} -> {new_stage}")
        
        # Update or create customer preferences (always update to store language and stage)
        if customer:
            cur.execute(
                "UPDATE Customers SET preferences = %s, qualification_stage = %s WHERE conversation_id = %s",
                (json.dumps(merged_preferences), new_stage, conversation_id)
            )
            logger.info(f"Updated customer preferences and stage for conversation {conversation_id}")
        else:
            cur.execute(
                "INSERT INTO Customers (conversation_id, preferences, qualification_stage) VALUES (%s, %s, %s)",
                (conversation_id, json.dumps(merged_preferences), new_stage)
            )
            logger.info(f"Created new customer for conversation {conversation_id}")
        conn.commit()
        existing_preferences = merged_preferences
        current_stage = new_stage
        
        cur.close()
        
        # Use existing preferences for context and queries
        preferences_context = json.dumps(existing_preferences)
        logger.info(f"Using preferences for query: {existing_preferences}")

        # Check if this is a greeting message FIRST (before checking preferences)
        greeting_keywords = ['hello', 'hi', 'hey', 'مرحبا', 'السلام عليكم', 'good morning', 'good evening']
        is_greeting = any(keyword.lower() in user_message.lower() for keyword in greeting_keywords)
        
        # Check if user is asking for apartments or has preferences
        apartment_keywords = ['apartment', 'شقة', 'unit', 'وحدة', 'bedroom', 'غرفة', 'budget', 'price', 'سعر', 'location', 'منطقة', 'available', 'متاح', 'show', 'عرض']
        has_apartment_intent = any(keyword in user_message.lower() for keyword in apartment_keywords)
        has_preferences = any(existing_preferences.get(key) for key in ['budget', 'bedrooms', 'location'])
        
        # DEBUG: Log the conditions
        logger.info(f"Debug for message '{user_message}': is_greeting={is_greeting}, has_apartment_intent={has_apartment_intent}, has_preferences={has_preferences}, is_pagination_request={is_pagination_request}")
        logger.info(f"existing_preferences: {existing_preferences}")
        
        # Only query for units if user has apartment intent or preferences, AND it's not just a greeting
        # Greetings should NOT trigger unit queries even if preferences exist
        units = []
        should_query_units = (has_apartment_intent or has_preferences or is_pagination_request or unit_search or has_feature_search) and not (is_greeting and not has_apartment_intent)
        logger.info(f"Should query units: {should_query_units} (unit_search: {unit_search}, has_feature_search: {has_feature_search})")
        
        if should_query_units:
            cur = conn.cursor()
            
            # Handle specific unit number search
            if unit_search:
                query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE unit_number = %s"
                params = [unit_search]
                logger.info(f"Unit number search for: {unit_search}")
                
            # Handle feature-based search with direct database search
            elif has_feature_search:
                logger.info(f"Performing feature-based search for: {user_message}")
                
                # Extract specific features mentioned in the message
                feature_conditions = []
                feature_params = []
                
                # Check for elevator (مصعد/elevator)
                if any(word in user_message.lower() for word in ['مصعد', 'elevator']):
                    feature_conditions.append("description_ar ILIKE %s")
                    feature_params.append("%مصعد%")
                    logger.info("Added elevator filter")
                
                # Check for balcony (بلكونة/balcony)  
                if any(word in user_message.lower() for word in ['بلكونة', 'بلكون', 'balcony']):
                    feature_conditions.append("description_ar ILIKE %s")
                    feature_params.append("%بلكون%")
                    logger.info("Added balcony filter")
                
                # Check for garage (كراج/garage)
                if any(word in user_message.lower() for word in ['كراج', 'garage', 'موقف']):
                    feature_conditions.append("description_ar ILIKE %s") 
                    feature_params.append("%كراج%")
                    logger.info("Added garage filter")
                
                # Check for terrace (تراس/terrace)
                if any(word in user_message.lower() for word in ['تراس', 'terrace']):
                    feature_conditions.append("description_ar ILIKE %s")
                    feature_params.append("%تراس%")
                    logger.info("Added terrace filter")
                
                # Build query with feature conditions
                if feature_conditions:
                    query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE " + " OR ".join(feature_conditions)
                    params = feature_params
                    logger.info(f"Feature search query: {query} with params: {feature_params}")
                else:
                    # Fallback to vector search if available
                    if vector_store:
                        logger.info("Trying vector search as fallback")
                        try:
                            search_results = vector_store.similarity_search(user_message, k=5)
                            unit_ids = []
                            for result in search_results:
                                if hasattr(result, 'metadata') and 'unit_id' in result.metadata:
                                    unit_ids.append(result.metadata['unit_id'])
                            
                            if unit_ids:
                                query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE unit_id = ANY(%s)"
                                params = [unit_ids]
                            else:
                                query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE 1=1"
                                params = []
                        except Exception as e:
                            logger.error(f"Vector search failed: {e}")
                            query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE 1=1"
                            params = []
                    else:
                        query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE 1=1"
                        params = []
                    
            # Regular preference-based search
            else:
                query = "SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units WHERE 1=1"
                params = []
                logger.info(f"Building query with preferences: {existing_preferences}")
                if existing_preferences.get("budget"):
                    query += " AND price_jod <= %s"
                    params.append(existing_preferences["budget"])
                    logger.info(f"Added budget filter: {existing_preferences['budget']}")
                if existing_preferences.get("bedrooms"):
                    query += " AND bedrooms = %s"
                    params.append(existing_preferences["bedrooms"])
                    logger.info(f"Added bedrooms filter: {existing_preferences['bedrooms']}")
                if existing_preferences.get("location"):
                    query += " AND address ILIKE %s"
                    params.append(f"%{existing_preferences['location']}%")
                    logger.info(f"Added location filter: {existing_preferences['location']}")
            
            logger.info(f"Final query: {query} with params: {params}")
            
            cur.execute(query, params)
            units = cur.fetchall()
            cur.close()
            
            logger.info(f"Query returned {len(units)} units")
        else:
            logger.info("No apartment intent or preferences detected, skipping unit query")

        # Implement pagination logic
        units_shown = existing_preferences.get("units_shown", [])
        units_per_page = 3
        
        # Filter out units that have already been shown
        available_units = [unit for unit in units if unit['unit_id'] not in units_shown]
        
        # Get the next batch of units to show
        units_to_show = available_units[:units_per_page]
        
        # Calculate pagination info
        total_units = len(units)
        total_shown = len(units_shown)
        units_being_shown = len(units_to_show)
        remaining_units = len(available_units) - units_being_shown
        
        logger.info(f"Pagination: Total={total_units}, Already shown={total_shown}, Showing now={units_being_shown}, Remaining={remaining_units}")

        unit_context = ""
        pagination_info = ""
        
        if units_to_show:
            unit_details = []
            newly_shown_unit_ids = []
            
            for unit in units_to_show:
                photos = unit['photos_urls'] if unit['photos_urls'] else []
                photo_text = ""
                if photos:
                    # Format photos as clickable links
                    photo_links = []
                    for i, photo in enumerate(photos[:2]):
                        photo_links.append(f"[Photo {i+1}]({photo})")
                    photo_text = f"\nPhotos: {', '.join(photo_links)}"
                
                unit_text = f"Unit {unit['unit_number'] or 'N/A'} at {unit['address']}, {unit['size_sqm']} sqm, {unit['price_jod']} JOD, {unit['bedrooms']} bedrooms{photo_text}\nDescription: {unit['description_ar'][:200]}..."
                unit_details.append(unit_text)
                newly_shown_unit_ids.append(unit['unit_id'])
            
            unit_context = "\n\n".join(unit_details)
            
            # Update units_shown in database
            updated_units_shown = units_shown + newly_shown_unit_ids
            existing_preferences["units_shown"] = updated_units_shown
            
            cur = conn.cursor()
            cur.execute(
                "UPDATE Customers SET preferences = %s WHERE conversation_id = %s",
                (json.dumps(existing_preferences), conversation_id)
            )
            conn.commit()
            cur.close()
            
            # Create pagination info for LLM
            if is_pagination_request:
                if remaining_units > 0:
                    pagination_info = f"Showing {units_being_shown} more apartments (total {total_shown + units_being_shown} shown out of {total_units} found). {remaining_units} more apartments available."
                else:
                    pagination_info = f"Showing {units_being_shown} more apartments (total {total_shown + units_being_shown} shown out of {total_units} found). These are all the apartments that match your criteria."
            else:
                if remaining_units > 0:
                    pagination_info = f"Showing {units_being_shown} of {total_units} apartments found. {remaining_units} more apartments available."
                else:
                    pagination_info = f"Showing all {total_units} apartments found."
            
            logger.info(f"Unit context created with pagination info: {pagination_info}")
        elif total_units > 0:
            # All units have been shown already
            unit_context = "You have already seen all the apartments that match your criteria."
            pagination_info = f"All {total_units} matching apartments have been shown."
            logger.info("All matching units have been shown")
        else:
            unit_context = "No apartments found matching the criteria."
            pagination_info = "No apartments found."
            logger.info("No units found, using default message")

        # Always use LLM for all conversations (no hardcoded responses)
        logger.info(f"🔍 Chat Debug - Message: '{user_message}'")
        logger.info(f"🔍 LLM available: {llm is not None}, AI settings available: {ai_settings is not None}")
        logger.info(f"🔍 unit_context preview: {unit_context[:100]}...")
        
        # Force LLM processing - both conditions are met
        logger.info(f"🔍 LLM check: llm={llm is not None}, ai_settings={ai_settings is not None}")
        if llm and ai_settings:
            logger.info("✅ Entering LLM processing path")
        else:
            logger.error(f"❌ LLM check failed: llm={llm}, ai_settings={ai_settings}")
            
        # ALWAYS USE LLM for all conversations (no fallbacks)
        if llm:
            logger.info("🚀 Using LLM for ALL conversations")
            try:
                # Build comprehensive context for LLM
                context_parts = []
                
                # Add customer qualification stage context
                context_parts.append(f"Customer Language: {detected_language.upper()}")
                context_parts.append(f"Qualification Stage: {current_stage}")
                
                # Add preferences context if available
                if existing_preferences:
                    context_parts.append(f"Customer Preferences: {json.dumps(existing_preferences)}")
                
                # Add unit context if available  
                if unit_context and unit_context != "No apartments found matching the criteria.":
                    context_parts.append(f"Available Units:\n{unit_context}")
                    if pagination_info:
                        context_parts.append(f"Pagination Info: {pagination_info}")
                
                context = "\n\n".join(context_parts)
                
                # Create comprehensive LLM prompt with qualification stage awareness
                system_prompt = f"""You are a professional real estate agent for BlueOlive Real Estate.

CUSTOMER CONTEXT:
{context}

QUALIFICATION STAGE TRACKING:
- Current Stage: {current_stage}
- Progress: initial → budget_collected → bedrooms_collected → location_collected → contact_info_collected

CRITICAL CONSTRAINT - ONLY USE DATABASE RESULTS:
- You can ONLY show apartments that are provided in the "Available Units" section above
- NEVER create, invent, or hallucinate apartment listings
- If no units are provided in the context, inform the customer that no matching apartments are available
- DO NOT make up unit names, prices, or features that are not in the database
- ONLY use the exact unit details, photos, and descriptions provided in the Available Units section

INSTRUCTIONS:
- Respond ONLY in {detected_language.upper()} language
- Be conversational, helpful, and professional
- If Arabic: Use casual, friendly tone (not formal) - use "كيف ممكن أساعدك؟" instead of formal expressions
- If customer is greeting (hello, hi, مرحبا), respond warmly and ask how you can help find an apartment
- Guide conversation based on current qualification stage:
  * initial: Ask about apartment requirements (budget, bedrooms, location)
  * budget_collected: Ask about bedrooms and location
  * bedrooms_collected: Ask about location and size preferences
  * location_collected: Show matching units and ask about contact info
  * contact_info_collected: Schedule viewings and provide additional assistance
- If units are available in the context, present them clearly with key details, photos, and descriptions
- Format photo links as clickable markdown links: [Photo 1](URL) for easy access
- If NO units are available, inform the customer and ask them to adjust their criteria
- Ask natural follow-up questions to progress the conversation
- If this is a pagination request, acknowledge it and show more units
- Focus on helping customer find their perfect apartment using ONLY real database results

CONVERSATION STYLE - IMPORTANT:
- When providing detailed information or multiple units, break your response into natural conversation parts
- Each part should feel like a separate message in a chat conversation (2-3 sentences maximum per part)
- For example, instead of one long response, send:
  1. Brief introduction/summary
  2. First unit details
  3. Second unit details  
  4. Follow-up question or call to action
- This creates a more natural, human-like conversation flow

Customer Message: "{user_message}"
"""
                
                logger.info(f"🎯 Sending to LLM: {system_prompt[:200]}...")
                
                from langchain_core.messages import HumanMessage, SystemMessage
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ])
                bot_response = response.content
                logger.info(f"✅ LLM response: {bot_response[:100]}...")
                
                # Log qualification stage and conversation tracking
                logger.info(f"📊 QUALIFICATION TRACKING:")
                logger.info(f"   - Conversation ID: {conversation_id}")
                logger.info(f"   - Current Stage: {current_stage}")
                logger.info(f"   - Language: {detected_language}")
                logger.info(f"   - User Message: {user_message}")
                logger.info(f"   - Preferences: {existing_preferences}")
                logger.info(f"   - Units Found: {len(units_to_show) if units_to_show else 0}")
                logger.info(f"   - Bot Response Length: {len(bot_response)} chars")
                
                # Store the chat
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO Chats (conversation_id, user_message, bot_response) VALUES (%s, %s, %s)",
                    (conversation_id, user_message, bot_response)
                )
                conn.commit()
                cur.close()
                conn.close()
                
                logger.info(f"💾 Chat stored successfully for conversation {conversation_id}")
                
                return {"conversation_id": conversation_id, "bot_response": bot_response}
                    
            except Exception as e:
                logger.error(f"❌ LLM processing failed: {str(e)}")
                # Continue to original logic below
            # Language-specific instructions
            language_instructions = {
                'ar': """
- Respond in Arabic only
- Use casual Arabic greetings: "مرحبا! كيف ممكن أساعدك؟"
- Format numbers and prices clearly in Arabic context
- Use casual, friendly Arabic language (not formal)
- Use everyday Arabic expressions and be conversational
""",
                'en': """
- Respond in English only  
- Use English greetings: "Hello! How can I help you?"
- Format numbers and prices clearly
- Use professional English language
"""
            }
            
            # Generate context-aware prompts based on qualification stage
            stage_prompts = {
                'initial': "This is a new customer. Greet them warmly and ask about their apartment requirements.",
                'budget_collected': f"Customer has provided budget ({existing_preferences.get('budget', 'N/A')} JOD). Now ask about bedrooms and location preferences.",
                'bedrooms_collected': f"Customer wants {existing_preferences.get('bedrooms', 'N/A')} bedrooms with budget {existing_preferences.get('budget', 'N/A')} JOD. Now ask about location preferences.",
                'location_collected': "Customer has provided budget, bedrooms, and location. Show matching units and ask if they'd like to schedule a viewing.",
                'contact_info_collected': "Customer has provided contact information. Offer to schedule viewings and provide next steps."
            }
            
            # LLM-based response with enhanced context
            system_prompt = f"""{ai_settings['prompt']}

Language Instructions:
{language_instructions.get(detected_language, language_instructions['en'])}

Current Customer Qualification Stage: {current_stage}
Stage Guidance: {stage_prompts.get(current_stage, stage_prompts['initial'])}

Current Customer Preferences: {preferences_context}

Pagination Information: {pagination_info}

Available Units Based on Preferences:
{unit_context}

AI Agent Instructions:
- You are a professional real estate agent helping customers find apartments
- Respond in {detected_language.upper()} language only
- Follow the stage guidance to ask appropriate follow-up questions
- If the user is just greeting (hello, hi, مرحبا, etc.), respond with a warm greeting and ask how you can help with their apartment search
- If units are available, present them in a clear, organized format with key details
- Guide the conversation toward collecting missing information (budget, bedrooms, location, contact info)
- Be conversational, helpful, and maintain a professional real estate agent persona
- Include unit numbers, addresses, sizes, prices, and key features when showing units
- When showing units, use the pagination information to naturally communicate how many units are available
- If more units are available, naturally offer to show them by saying something like "Would you like to see more options?" or "I have more apartments that might interest you"
- If this is a pagination request, acknowledge it naturally and present the new units
- Always maintain conversation context and remember what has been shown before
- IMPORTANT: Only show apartments when the user has expressed interest in apartment search, NOT for general greetings

CONVERSATION STYLE - IMPORTANT:
- When providing detailed information or multiple units, break your response into natural conversation parts
- Each part should feel like a separate message in a chat conversation (2-3 sentences maximum per part)
- For example, instead of one long response, send:
  1. Brief introduction/summary
  2. First unit details
  3. Second unit details  
  4. Follow-up question or call to action
- This creates a more natural, human-like conversation flow
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
                    if units_to_show:
                        if is_pagination_request:
                            if remaining_units > 0:
                                bot_response = f"Here are {units_being_shown} more apartments:\n{unit_context}\n\nI have {remaining_units} more apartments available. Would you like to see more?"
                            else:
                                bot_response = f"Here are the last {units_being_shown} apartments:\n{unit_context}\n\nThese are all the apartments that match your criteria."
                        else:
                            if remaining_units > 0:
                                bot_response = f"{pagination_info}\n{unit_context}\n\nWould you like to see more options?"
                            else:
                                bot_response = f"{pagination_info}\n{unit_context}"
                    elif total_units > 0:
                        bot_response = unit_context  # "You have already seen all the apartments..."
                    else:
                        bot_response = "No apartments found matching your criteria. Please provide more details like budget, bedrooms, or location."
                        
            except Exception as e:
                logger.error(f"LLM failed: {str(e)}")
                # Rule-based fallback
                if units_to_show:
                    if is_pagination_request:
                        if remaining_units > 0:
                            bot_response = f"Here are {units_being_shown} more apartments:\n{unit_context}\n\nI have {remaining_units} more apartments available. Would you like to see more?"
                        else:
                            bot_response = f"Here are the last {units_being_shown} apartments:\n{unit_context}\n\nThese are all the apartments that match your criteria."
                    else:
                        if remaining_units > 0:
                            bot_response = f"{pagination_info}\n{unit_context}\n\nWould you like to see more options?"
                        else:
                            bot_response = f"{pagination_info}\n{unit_context}"
                elif total_units > 0:
                    bot_response = unit_context  # "You have already seen all the apartments..."
                else:
                    bot_response = "No apartments found matching your criteria. Please provide more details like budget, bedrooms, or location."
        else:
            # Rule-based response when no LLM
            logger.error(f"❌ LLM not available! llm={llm is not None}, ai_settings={ai_settings is not None}")
            logger.error("💥 Using fallback rule-based responses instead of AI conversation")
            # Rule-based responses when LLM is not available
            # Handle greetings even when LLM is not available
            if is_greeting and not has_apartment_intent and not units_to_show:
                if detected_language == 'ar':
                    bot_response = "مرحبا! أنا وكيل عقارات متخصص في شركة BlueOlive. كيف يمكنني مساعدتك في العثور على الشقة المثالية؟"
                else:
                    bot_response = "Hello! I'm a real estate agent with BlueOlive. How can I help you find the perfect apartment today?"
            elif units_to_show:
                if is_pagination_request:
                    if remaining_units > 0:
                        bot_response = f"Here are {units_being_shown} more apartments:\n{unit_context}\n\nI have {remaining_units} more apartments available. Would you like to see more?"
                    else:
                        bot_response = f"Here are the last {units_being_shown} apartments:\n{unit_context}\n\nThese are all the apartments that match your criteria."
                else:
                    if remaining_units > 0:
                        bot_response = f"{pagination_info}\n{unit_context}\n\nWould you like to see more options?"
                    else:
                        bot_response = f"{pagination_info}\n{unit_context}"
            elif total_units > 0:
                bot_response = unit_context  # "You have already seen all the apartments..."
            elif has_apartment_intent:
                bot_response = "I'd be happy to help you find an apartment! Could you tell me your preferences for budget, number of bedrooms, and preferred location?"
            else:
                bot_response = "Hello! I'm here to help you find the perfect apartment. Could you tell me what you're looking for?"

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
        chat_result = cur.fetchone()
        chat_id = chat_result['chat_id'] if chat_result else None
        conn.commit()
        cur.close()
        conn.close()

        return {"conversation_id": conversation_id, "bot_response": bot_response}
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
