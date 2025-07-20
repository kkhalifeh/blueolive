# DATA.md - BlueOlive Real Estate Data Management Guide

This document provides comprehensive instructions for managing data in the BlueOlive Real Estate AI Agent system, including database schema, data preparation, and vector embedding processes.

## 📊 Database Schema Overview

### Units Table Structure

The main `Units` table contains all property information with the following columns:

```sql
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
```

## 📋 Required Data Columns

When preparing new data for import, ensure your Excel/CSV file contains these columns:

### ✅ **REQUIRED COLUMNS**

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `unit_number` | VARCHAR(20) | Unique unit identifier | "117", "110A", "B-205" |
| `address` | TEXT | Full property address | "ابو علندا - دوار الحكمة" |
| `size_sqm` | FLOAT | Unit size in square meters | 117.5 |
| `bedrooms` | INTEGER | Number of bedrooms | 3 |
| `bathrooms` | INTEGER | Number of bathrooms | 3 |
| `price_jod` | FLOAT | Price in Jordanian Dinars | 52000.0 |
| `description_ar` | TEXT | **Arabic description** (CRITICAL for vector search) | "شقة مميزة مع مصعد وكراج..." |

### 🔧 **OPTIONAL COLUMNS**

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `project_id` | INTEGER | Project reference ID | 1, 2, 3 |
| `floor_type` | VARCHAR(20) | Floor type/level | "طابق ثاني", "مع روف" |
| `floor_number` | INTEGER | Floor number | 2, 3, -1 (basement) |
| `delivery_status` | VARCHAR(50) | Construction status | "جاهز", "تحت الإنشاء" |
| `description_en` | TEXT | English description | "Beautiful apartment with..." |
| `features` | JSONB | Additional features | {"parking": true, "elevator": true} |
| `photos_urls` | TEXT[] | Facebook photo URLs | ["https://facebook.com/..."] |
| `video_urls` | TEXT[] | Video URLs | ["https://youtube.com/..."] |

## 🗺️ **Location & Coordinates**

The system uses PostGIS for geospatial data:

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `location` | GEOMETRY(POINT, 4326) | GPS coordinates | POINT(35.9106 32.0569) |

**Note**: Location coordinates are auto-generated from addresses using geocoding scripts.

## 🔍 **Vector Embeddings - CRITICAL for Search**

The `embedding_vector VECTOR(384)` column is essential for:
- **Semantic search** (finding apartments by features)
- **Feature matching** (balcony, garage, elevator, view)
- **Natural language queries** in Arabic and English

### **What Gets Vectorized**
The vector embeddings are generated from the **Arabic description** (`description_ar`) because it contains the most detailed information about:
- ✅ **Features**: مصعد (elevator), كراج (garage), بلكونة (balcony)
- ✅ **Amenities**: تشطيب سوبر ديلوكس, إطلالة بانوراما
- ✅ **Location details**: منطقة هادئة, قريب من الخدمات
- ✅ **Building specs**: حجر رويشد, جبسن بورد موديرن

## 📥 Data Import Process

### Step 1: Prepare Your Data

**Excel/CSV Format:**
```csv
unit_number,address,size_sqm,bedrooms,bathrooms,price_jod,description_ar,photos_urls
117,"ابو علندا - دوار الحكمة",117,3,3,50000,"شقة مميزة 117م في اجمل مناطق ابو علندا...","https://facebook.com/..."
110,"ابو علندا - دوار الحكمة",110,3,3,52000,"عرض مغري شقة فاخره تشطيب سوبر ديلوكس...","https://facebook.com/..."
```

### Step 2: Data Validation

Before importing, verify:
- ✅ **All required columns** are present
- ✅ **Arabic descriptions** are detailed and include features
- ✅ **Price and size** are numeric values
- ✅ **Photo URLs** are valid Facebook links
- ✅ **Unit numbers** are unique within each project

### Step 3: Database Import

Use the provided migration script:

```bash
# Convert Excel to CSV
python scripts/convert_excel_to_csv.py

# Import data to database
python scripts/migrate_data.py

# Update coordinates (geocoding)
python scripts/update_coordinates.py
```

### Step 4: Generate Vector Embeddings

**CRITICAL STEP**: After importing data, generate embeddings:

```bash
# Generate embeddings for new units
python scripts/repopulate_embeddings.py
```

## 🤖 Vector Embedding Generation Script

Create/update `scripts/generate_embeddings.py`:

```python
import psycopg2
from sentence_transformers import SentenceTransformer
import json
import logging

# Configuration
DATABASE_URL = "postgresql://blueolive:securepassword@localhost:5432/blueolive_db"
MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dimensional embeddings

def generate_embeddings():
    """Generate embeddings for all units without embeddings"""
    
    # Initialize model
    model = SentenceTransformer(MODEL_NAME)
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get units without embeddings
    cur.execute("""
        SELECT unit_id, description_ar 
        FROM Units 
        WHERE embedding_vector IS NULL 
        AND description_ar IS NOT NULL
    """)
    
    units = cur.fetchall()
    print(f"Found {len(units)} units needing embeddings")
    
    for unit_id, description_ar in units:
        try:
            # Generate embedding
            embedding = model.encode(description_ar)
            embedding_list = embedding.tolist()
            
            # Update database
            cur.execute("""
                UPDATE Units 
                SET embedding_vector = %s 
                WHERE unit_id = %s
            """, (embedding_list, unit_id))
            
            print(f"✅ Generated embedding for unit {unit_id}")
            
        except Exception as e:
            print(f"❌ Error for unit {unit_id}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print("🎉 Embedding generation complete!")

if __name__ == "__main__":
    generate_embeddings()
```

## 🔄 Update Existing Data

### Adding New Units

1. **Prepare new data** in CSV format with all required columns
2. **Import to database** using migration scripts
3. **Generate embeddings** for new units:
   ```bash
   python scripts/generate_embeddings.py
   ```

### Updating Existing Units

1. **Update database** directly or via CSV import
2. **Clear existing embeddings** for updated units:
   ```sql
   UPDATE Units SET embedding_vector = NULL WHERE unit_id IN (1,2,3);
   ```
3. **Regenerate embeddings**:
   ```bash
   python scripts/generate_embeddings.py
   ```

## 🏗️ Projects Table

For organizing units by project:

```sql
CREATE TABLE Projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Example projects:
```sql
INSERT INTO Projects (project_name, description) VALUES 
('ابو علندا - دوار الحكمة', 'Luxury apartments in Abu Alanda'),
('حي المنصور - شارع ياجوز', 'Modern units in Mansour district'),
('ضاحية الرشيد', 'Premium residences in Rashid suburb');
```

## 🔍 Search Capabilities

With proper data structure and embeddings, the system supports:

### **Basic Filtering**
- Budget: `price_jod <= budget`
- Bedrooms: `bedrooms = count`
- Location: `address ILIKE '%location%'`

### **Unit Number Search**
- Direct: `unit_number = '117'`
- Natural: "tell me about unit 117"

### **Feature-Based Search** (Requires Embeddings)
- English: "apartment with balcony and garage"
- Arabic: "شقة فيها مصعد وكراج"
- Features: elevator, balcony, garage, view, terrace

## ⚠️ Important Notes

### **Data Quality Requirements**

1. **Arabic Descriptions are CRITICAL**
   - Must be detailed and include all features
   - Use specific terms: مصعد, كراج, بلكونة, إطلالة
   - Include building specs and amenities

2. **Consistent Address Format**
   - Use standardized location names
   - Include area and landmark: "ابو علندا - دوار الحكمة"

3. **Photo URLs**
   - Prefer Facebook business page URLs
   - Ensure URLs are accessible
   - Include multiple photos when available

### **Vector Search Optimization**

- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Language**: Optimized for Arabic content
- **Features**: Best results with detailed Arabic descriptions
- **Updates**: Regenerate embeddings after description changes

## 📋 Data Checklist

Before going live with new data:

- [ ] All required columns present
- [ ] Arabic descriptions detailed and feature-rich
- [ ] Unit numbers unique within projects
- [ ] Photo URLs tested and accessible
- [ ] Database import successful
- [ ] Coordinates generated (if needed)
- [ ] **Vector embeddings generated** ⚠️ CRITICAL
- [ ] Search functionality tested
- [ ] Both Arabic and English searches working

## 🔧 Maintenance Scripts

Keep these scripts updated in the `scripts/` directory:

- `convert_excel_to_csv.py` - Excel to CSV conversion
- `migrate_data.py` - Database import
- `update_coordinates.py` - Geocoding
- `generate_embeddings.py` - Vector embedding generation
- `repopulate_embeddings.py` - Batch embedding updates

## 🚀 Quick Start for New Data

```bash
# 1. Place your Excel file in the project root
# 2. Convert and import
python scripts/convert_excel_to_csv.py
python scripts/migrate_data.py

# 3. Generate embeddings (CRITICAL)
python scripts/generate_embeddings.py

# 4. Test the system
curl -X POST http://localhost:8000/chat -d '{"message": "tell me about unit 117"}'
```

---

**🎯 Remember**: The vector embeddings are what make the advanced search features work. Without them, users can only search by basic criteria (budget, bedrooms, location) but cannot find units by features or get specific unit information.