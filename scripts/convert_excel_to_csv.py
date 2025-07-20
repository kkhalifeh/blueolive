import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # Read Excel file
        excel_file = "Copy of نموذج AI شقق.xlsx"
        df = pd.read_excel(excel_file, sheet_name="Sheet1")
        logger.info(f"Loaded Excel file with {len(df)} rows")

        # Rename columns to match expected format
        df = df.rename(columns={
            'No.': 'unit_id',
            'Google Coordinates (الإحداثيات عبر Google)': 'google_maps_url'
        })

        # Select only relevant columns
        df = df[['unit_id', 'google_maps_url']]

        # Save to CSV
        csv_file = "unit_coordinates.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"Saved CSV to {csv_file}")

    except Exception as e:
        logger.error(f"Error converting Excel to CSV: {e}")

if __name__ == "__main__":
    main()
