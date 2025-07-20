import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import PGVector
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": "blueolive_db",
    "user": "blueolive",
    "password": "securepassword",
    "host": "localhost",
    "port": "5432"
}
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

def main():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Fetch units
        cur.execute("SELECT unit_id, description_ar FROM Units")
        units = cur.fetchall()

        # Initialize vector store
        embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = PGVector(
            connection_string="postgresql://blueolive:securepassword@localhost:5432/blueolive_db",
            embedding_function=embedding_function,
            collection_name="units",
            distance_strategy="cosine"
        )

        # Clear existing embeddings
        cur.execute("DELETE FROM langchain_pg_embedding WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = 'units')")
        conn.commit()

        # Insert new embeddings
        for unit in units:
            unit_id = unit['unit_id']
            description = unit['description_ar']
            vector_store.add_texts(
                texts=[description],
                metadatas=[{
                    "unit_id": unit_id,
                    "unit_number": unit.get('unit_number', 'N/A'),
                    "address": unit.get('address', ''),
                    "size_sqm": unit.get('size_sqm', 0.0),
                    "price_jod": unit.get('price_jod', 0.0)
                }],
                ids=[str(unit_id)]
            )
            logger.info(f"Added embedding for unit_id {unit_id}")

        conn.commit()
        logger.info("Embeddings repopulated successfully")
    except Exception as e:
        logger.error(f"Error repopulating embeddings: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
