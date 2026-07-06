import os
import sqlite3

class AgriDataMCPServer:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "database.db")
        
    def _get_connection(self):
        # Using check_same_thread=False for FastAPI compatibility
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def get_soil_requirements(self, crop_name):
        """
        Retrieves ideal soil metrics (N, P, K, pH) and crop water coefficient (Kc).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM soil_standards WHERE crop_name = ?", (crop_name,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {"error": f"Crop '{crop_name}' not found in standard requirements."}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_weather_data(self, region_id, forecast_date):
        """
        Retrieves weather parameters for a specific region and date.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT temp_c, humidity, precip_mm, solar_radiation FROM weather_forecast WHERE region_id = ? AND forecast_date = ?", 
                (region_id, forecast_date)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            # Default weather values to handle missing records safely
            return {
                "temp_c": 25.0,
                "humidity": 60.0,
                "precip_mm": 0.0,
                "solar_radiation": 18.0,
                "note": "Default weather fallback"
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_market_prices(self, crop_name, region_id):
        """
        Retrieves weekly market price history for a crop in a region.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT date, price_per_metric_ton FROM market_trends WHERE crop_name = ? AND region_id = ? ORDER BY date DESC LIMIT 6",
                (crop_name, region_id)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_ecological_restrictions(self):
        """
        Retrieves regulatory limits for chemicals.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM regulated_chemicals")
            rows = cursor.fetchall()
            return {r['chemical_id']: {"name": r['chemical_name'], "max_limit": r['max_safe_dosage_kg_hectare'], "is_restricted": r['is_restricted']} for r in rows}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_crop_suitability(self, region_id, crop_name):
        """
        Check suitability score for a specific crop and region.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT suitability_score FROM regional_crop_suitability WHERE region_id = ? AND crop_name = ?",
                (region_id, crop_name)
            )
            row = cursor.fetchone()
            if row:
                return float(row['suitability_score'])
            return 0.5  # Neutral suitability fallback
        except Exception as e:
            return 0.5
        finally:
            conn.close()

# In case we want to launch this as a formal standard MCP Server using Python mcp
# Command implementation for local development
def run_mcp_service():
    from mcp.server.fastmcp import FastMCP
    mcp_app = FastMCP("AgriGuard Database MCP Server")
    server = AgriDataMCPServer()
    
    @mcp_app.tool()
    def fetch_soil_standards(crop: str) -> dict:
        """Fetch NPK and pH specifications for a crop."""
        return server.get_soil_requirements(crop)
        
    @mcp_app.tool()
    def fetch_weather(region: str, date: str) -> dict:
        """Fetch temperature and rainfall for a region on a specific date."""
        return server.get_weather_data(region, date)
        
    @mcp_app.tool()
    def fetch_prices(crop: str, region: str) -> list:
        """Fetch the latest wholesale price history."""
        return server.get_market_prices(crop, region)
        
    @mcp_app.tool()
    def fetch_ecology_limits() -> dict:
        """Fetch safety limits and restrictions for chemical substances."""
        return server.get_ecological_restrictions()

    # In production, we run via FastMCP entry point
    pass

if __name__ == "__main__":
    # Test server locally
    srv = AgriDataMCPServer()
    print("Soil Requirements (Rice):", srv.get_soil_requirements("Rice"))
    print("Ecological limits:", srv.get_ecological_restrictions())
