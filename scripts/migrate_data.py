import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import re
import json
import logging
import time
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_CONFIG = {
    "dbname": "blueolive_db",
    "user": "blueolive",
    "password": "securepassword",
    "host": "localhost",
    "port": "5432"
}
CSV_FILE = "./Cleaned_Real_Estate_Data_Sample.csv"
MODEL = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dimensional embeddings

def clean_apartment_number(apartment_number):
    try:
        match = re.match(r"(\d+م)?\s*(.*)", str(apartment_number))
        size = match.group(1).replace("م", "") if match.group(1) else None
        floor_type = match.group(2).strip() if match.group(2) else None
        return size, floor_type
    except Exception as e:
        logger.error(f"Error parsing apartment_number {apartment_number}: {e}")
        return None, None

def extract_coordinates_from_google_maps(url):
    try:
        if pd.isna(url):
            return None
        response = requests.get(url, allow_redirects=True, timeout=10)
        full_url = response.url
        logger.info(f"Resolved URL: {full_url}")
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', full_url)
        if match:
            lat, lon = match.groups()
            logger.info(f"Extracted coordinates from {url}: ({lat}, {lon})")
            return f"SRID=4326;POINT({lon} {lat})"
        logger.warning(f"No coordinates found in {full_url}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Google Maps URL {url}: {e}")
        return None

def extract_features(description, notes):
    features = {}
    description = str(description) if pd.notna(description) else ""
    notes = str(notes) if pd.notna(notes) else ""
    if "بلكونة" in description or "بلكونتين" in description or "برندة" in description:
        features["balconies"] = 2 if "بلكونتين" in description else 1
    if "غرفة خادمة" in description or "غرفة خادمة" in notes:
        features["maid_room"] = True
    if "اطلالة مميزة" in notes or "إطلالة بانورامية" in description:
        features["view"] = "panoramic"
    return features

def main():
    logger.info("Starting data migration")
    try:
        # Load CSV
        df = pd.read_csv(CSV_FILE)
        logger.info(f"Loaded CSV with {len(df)} rows")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check for existing units to avoid duplicates
        cur.execute("SELECT project_id, unit_number, address, size_sqm, price_jod FROM Units")
        existing_units = {(row[0], row[1], row[2], row[3], row[4]) for row in cur.fetchall()}

        # Process projects
        projects = df['project_name'].unique()
        project_map = {}
        for project in projects:
            try:
                cur.execute(
                    "SELECT project_id FROM Projects WHERE project_name = %s",
                    (project,)
                )
                result = cur.fetchone()
                if result:
                    project_map[project] = result[0]
                else:
                    cur.execute(
                        "INSERT INTO Projects (project_name) VALUES (%s) RETURNING project_id",
                        (project,)
                    )
                    project_map[project] = cur.fetchone()[0]
            except Exception as e:
                logger.error(f"Error processing project {project}: {e}")
                continue

        # Process units and contacts
        for idx, row in df.iterrows():
            try:
                size, floor_type = clean_apartment_number(row['apartment_number'])
                project_id = project_map.get(row['project_name'])
                if not project_id:
                    logger.warning(f"No project_id for {row['project_name']}, skipping row {idx}")
                    continue
                if (project_id, size, row['address'], row['size_sqm'], row['price_jod']) in existing_units:
                    logger.info(f"Skipping duplicate unit: {row['project_name']}, {size}, {row['address']}, {row['size_sqm']} sqm, {row['price_jod']} JOD")
                    continue

                google_maps_url = row.get('google_maps_url', None)
                location = extract_coordinates_from_google_maps(google_maps_url) if google_maps_url else None
                features = extract_features(row['description'], row['notes'])
                embedding = MODEL.encode(row['description']).tolist() if pd.notna(row['description']) else None

                # Insert unit
                cur.execute(
                    """
                    INSERT INTO Units (
                        project_id, unit_number, address, location, size_sqm, bedrooms, bathrooms,
                        floor_type, floor_number, price_jod, delivery_status, description_ar,
                        features, photos_urls, embedding_vector
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING unit_id
                    """,
                    (
                        project_id, size, row['address'], location,
                        row['size_sqm'], row['bedrooms'], row['bathrooms'], floor_type,
                        row['floor'], row['price_jod'], row['delivery_status'], row['description'],
                        json.dumps(features), [row['photos_url']] if pd.notna(row['photos_url']) else [],
                        embedding
                    )
                )
                unit_id = cur.fetchone()[0]
                logger.info(f"Inserted unit {unit_id} for {row['address']}")

                # Insert contacts
                if pd.notna(row['responsible_name']):
                    cur.execute(
                        """
                        INSERT INTO Contacts (unit_id, contact_type, name, phone_number, email)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (unit_id, 'responsible', row['responsible_name'], row['phone_number'], row['email'])
                    )
                if pd.notna(row['guard_phone']):
                    cur.execute(
                        """
                        INSERT INTO Contacts (unit_id, contact_type, phone_number)
                        VALUES (%s, %s, %s)
                        """,
                        (unit_id, 'guard', row['guard_phone'])
                    )
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                continue

        conn.commit()
        logger.info("Data migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
