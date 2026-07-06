import os
import sqlite3
from datetime import datetime, timedelta

def seed_database():
    db_dir = os.path.join(os.path.dirname(__file__), "mcp_server")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "database.db")
    
    print(f"Initializing database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Create Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regions (
        region_id TEXT PRIMARY KEY,
        region_name TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crops (
        crop_name TEXT PRIMARY KEY
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS soil_standards (
        crop_name TEXT PRIMARY KEY,
        ideal_n REAL,
        ideal_p REAL,
        ideal_k REAL,
        min_ph REAL,
        max_ph REAL,
        kc_coefficient REAL,
        FOREIGN KEY(crop_name) REFERENCES crops(crop_name)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regional_crop_suitability (
        region_id TEXT,
        crop_name TEXT,
        suitability_score REAL,
        PRIMARY KEY (region_id, crop_name),
        FOREIGN KEY(region_id) REFERENCES regions(region_id),
        FOREIGN KEY(crop_name) REFERENCES crops(crop_name)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regulated_chemicals (
        chemical_id TEXT PRIMARY KEY,
        chemical_name TEXT,
        max_safe_dosage_kg_hectare REAL,
        is_restricted INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crop_chemical_usage (
        crop_name TEXT,
        chemical_id TEXT,
        application_purpose TEXT,
        recommended_base_dosage_kg_hectare REAL,
        PRIMARY KEY (crop_name, chemical_id),
        FOREIGN KEY(crop_name) REFERENCES crops(crop_name),
        FOREIGN KEY(chemical_id) REFERENCES regulated_chemicals(chemical_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_forecast (
        region_id TEXT,
        forecast_date TEXT,
        temp_c REAL,
        humidity REAL,
        precip_mm REAL,
        solar_radiation REAL,
        PRIMARY KEY (region_id, forecast_date),
        FOREIGN KEY(region_id) REFERENCES regions(region_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_trends (
        crop_name TEXT,
        region_id TEXT,
        date TEXT,
        price_per_metric_ton REAL,
        PRIMARY KEY (crop_name, region_id, date),
        FOREIGN KEY(crop_name) REFERENCES crops(crop_name),
        FOREIGN KEY(region_id) REFERENCES regions(region_id)
    )
    """)
    
    # 2. Insert Data
    
    # Regions
    regions = [
        ("ZONE_NORTH", "North Agricultural Plains"),
        ("ZONE_SOUTH", "South Wetlands"),
        ("ZONE_VALLEY", "Temperate Central Valley")
    ]
    cursor.executemany("INSERT OR REPLACE INTO regions VALUES (?, ?)", regions)
    
    # Crops
    crops = [("Wheat",), ("Rice",), ("Maize",), ("Tomato",), ("Potato",), ("Soybeans",)]
    cursor.executemany("INSERT OR REPLACE INTO crops VALUES (?)", crops)
    
    # Soil standards
    soil_standards = [
        # crop_name, ideal_n, ideal_p, ideal_k, min_ph, max_ph, kc_coefficient
        ("Wheat", 80.0, 40.0, 40.0, 6.0, 7.0, 1.15),
        ("Rice", 100.0, 50.0, 50.0, 5.5, 6.5, 1.20),
        ("Maize", 120.0, 60.0, 60.0, 5.8, 7.0, 1.20),
        ("Tomato", 140.0, 80.0, 100.0, 6.0, 6.8, 1.15),
        ("Potato", 110.0, 70.0, 120.0, 5.0, 6.0, 1.15),
        ("Soybeans", 30.0, 60.0, 80.0, 6.0, 7.0, 1.15)
    ]
    cursor.executemany("INSERT OR REPLACE INTO soil_standards VALUES (?, ?, ?, ?, ?, ?, ?)", soil_standards)
    
    # Suitability scores
    suitability = [
        ("ZONE_NORTH", "Wheat", 0.90),
        ("ZONE_NORTH", "Maize", 0.75),
        ("ZONE_NORTH", "Potato", 0.60),
        ("ZONE_SOUTH", "Rice", 0.95),
        ("ZONE_SOUTH", "Soybeans", 0.70),
        ("ZONE_VALLEY", "Tomato", 0.90),
        ("ZONE_VALLEY", "Maize", 0.85),
        ("ZONE_VALLEY", "Wheat", 0.70),
        ("ZONE_VALLEY", "Potato", 0.80)
    ]
    cursor.executemany("INSERT OR REPLACE INTO regional_crop_suitability VALUES (?, ?, ?)", suitability)
    
    # Regulated chemicals
    chemicals = [
        # chemical_id, chemical_name, max_safe_dosage_kg_hectare, is_restricted
        ("UREA", "Urea Fertilizer (N Source)", 300.0, 0),
        ("DAP", "Diammonium Phosphate (P Source)", 250.0, 0),
        ("MOP", "Muriate of Potash (K Source)", 200.0, 0),
        ("GLYPHOSATE", "Glyphosate (Herbicide)", 2.5, 1),
        ("IMIDACLOPRID", "Imidacloprid (Insecticide)", 0.5, 1),
        ("ORGANIC_COMPOST", "Organic Animal/Plant Compost", 5000.0, 0)
    ]
    cursor.executemany("INSERT OR REPLACE INTO regulated_chemicals VALUES (?, ?, ?, ?)", chemicals)
    
    # Crop chemical usage
    crop_chemicals = [
        ("Rice", "UREA", "nitrogen_source", 150.0),
        ("Rice", "DAP", "phosphorus_source", 100.0),
        ("Rice", "MOP", "potash_source", 80.0),
        ("Rice", "GLYPHOSATE", "weed_control", 1.2),
        ("Wheat", "UREA", "nitrogen_source", 120.0),
        ("Wheat", "DAP", "phosphorus_source", 80.0),
        ("Wheat", "MOP", "potash_source", 60.0),
        ("Tomato", "UREA", "nitrogen_source", 140.0),
        ("Tomato", "DAP", "phosphorus_source", 120.0),
        ("Tomato", "MOP", "potash_source", 150.0),
        ("Tomato", "IMIDACLOPRID", "pest_control", 0.3)
    ]
    cursor.executemany("INSERT OR REPLACE INTO crop_chemical_usage VALUES (?, ?, ?, ?)", crop_chemicals)
    
    # Weather Forecast (Generates a 7-day forecast starting from today)
    today = datetime.now()
    weather_data = []
    
    # Zone North (Dry/Sunny)
    for i in range(7):
        date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        weather_data.append(("ZONE_NORTH", date_str, 32.5 + i*0.2, 45.0 - i*0.5, 0.0, 24.5))
        
    # Zone South (Rainy/Humid)
    for i in range(7):
        date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        precip = 12.0 if i in [1, 3, 5] else 2.0
        weather_data.append(("ZONE_SOUTH", date_str, 26.0 - i*0.1, 85.0 + i*0.5, precip, 14.0))
        
    # Zone Valley (Mild/Favorable)
    for i in range(7):
        date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        precip = 1.5 if i == 4 else 0.0
        weather_data.append(("ZONE_VALLEY", date_str, 22.0 + i*0.1, 60.0 + i*0.2, precip, 19.5))
        
    cursor.executemany("INSERT OR REPLACE INTO weather_forecast VALUES (?, ?, ?, ?, ?, ?)", weather_data)
    
    # Market Trends (Historical prices for past 6 weeks)
    market_data = []
    for week in range(6):
        date_str = (today - timedelta(weeks=week)).strftime("%Y-%m-%d")
        # Crop, Region, Date, Price/MetricTon
        market_data.extend([
            ("Wheat", "ZONE_NORTH", date_str, 240.0 - week * 2.5),
            ("Wheat", "ZONE_VALLEY", date_str, 255.0 - week * 1.5),
            ("Rice", "ZONE_SOUTH", date_str, 310.0 + week * 3.0),
            ("Maize", "ZONE_NORTH", date_str, 190.0 - week * 1.0),
            ("Maize", "ZONE_VALLEY", date_str, 205.0 + week * 0.5),
            ("Tomato", "ZONE_VALLEY", date_str, 450.0 + week * 8.0),
            ("Potato", "ZONE_VALLEY", date_str, 180.0 - week * 2.0)
        ])
        
    cursor.executemany("INSERT OR REPLACE INTO market_trends VALUES (?, ?, ?, ?)", market_data)
    
    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
