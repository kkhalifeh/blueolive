from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Initialize FastAPI
app = FastAPI()

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Pydantic model for unit response
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
        raise HTTPException(status_code=500, detail=f"Error fetching units: {str(e)}")

# Admin endpoint to list units
@app.get("/admin/units", response_model=list[Unit])
async def get_admin_units():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT unit_id, project_id, unit_number, address, size_sqm, price_jod, bedrooms, bathrooms, floor_type, floor_number, description_ar, photos_urls FROM Units")
        units = cur.fetchall()
        cur.close()
        conn.close()
        return units
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin units: {str(e)}")
