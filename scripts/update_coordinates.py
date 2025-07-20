import pandas as pd
import psycopg2
import re
import requests
import logging

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
EXCEL_FILE = "Copy of نموذج AI شقق.xlsx"

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

def main():
    logger.info("Starting coordinate update")
    try:
        # Load Excel
        df = pd.read_excel(EXCEL_FILE, sheet_name="Sheet1")
        logger.info(f"Loaded Excel with {len(df)} rows")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Map rows to unit_id using address, size_sqm, price_jod
        cur.execute("SELECT unit_id, address, size_sqm, price_jod FROM Units")
        unit_map = { (row[1], row[2], row[3]): row[0] for row in cur.fetchall() }

        # Update units with coordinates
        for idx, row in df.iterrows():
            try:
                key = (row['Location (Full Address) (الموقع الكامل)'], 
                       float(row['Apartment Size (sqm) (مساحة الشقة م²)'].replace('م', '')), 
                       row['Price in JOD (السعر بالدينار)'])
                if key not in unit_map:
                    logger.warning(f"No matching unit found for {key}")
                    continue
                unit_id = unit_map[key]
                location = extract_coordinates_from_google_maps(row['Google Coordinates (الإحداثيات عبر Google)'])
                if location:
                    cur.execute(
                        "UPDATE Units SET location = %s WHERE unit_id = %s",
                        (location, unit_id)
                    )
                    logger.info(f"Updated location for unit_id {unit_id}")
                else:
                    logger.warning(f"No location updated for unit_id {unit_id}")
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                continue

        conn.commit()
        logger.info("Coordinate update completed successfully")
    except Exception as e:
        logger.error(f"Update failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
