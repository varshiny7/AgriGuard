def calculate_irrigation(temp_c, humidity, precip_mm, solar_radiation, kc, farm_size_hectares=1.0):
    """
    Calculates reference evapotranspiration (ET0) using Hargreaves-Samani model
    and determines the net watering volume needed in Liters.
    
    temp_c: Average temperature in Celsius
    humidity: Relative humidity percentage
    precip_mm: Precipitation (rainfall) in mm
    solar_radiation: Extraterrestrial radiation equivalent (Ra in mm/day)
    kc: Crop coefficient (from crop database)
    farm_size_hectares: Total farm size in Hectares (default: 1.0)
    
    Returns:
    dict containing:
        - 'et0_mm_day': float
        - 'etc_mm_day': float
        - 'net_irrigation_depth_mm': float
        - 'irrigation_volume_liters': float
    """
    try:
        # 1. Estimate ET0 using Hargreaves-Samani (simplified using solar_radiation as Ra)
        # Standard Hargreaves-Samani estimation:
        # We approximate T_max - T_min using humidity (higher humidity -> lower range, lower humidity -> higher range)
        temp_range = 12.0
        if humidity > 80:
            temp_range = 6.0
        elif humidity < 40:
            temp_range = 16.0
            
        t_mean = temp_c
        
        # Hargreaves-Samani equation:
        et0 = 0.0023 * (t_mean + 17.8) * (temp_range ** 0.5) * solar_radiation
        et0 = max(0.0, et0)
        
        # 2. Crop evapotranspiration
        etc = et0 * kc
        
        # 3. Effective Rainfall (USDA Soil Conservation Service method)
        # Simplified: 80% of precip is usable by soil
        effective_precip = precip_mm * 0.8
        
        # 4. Net Irrigation Depth needed
        net_irr_depth = max(0.0, etc - effective_precip)
        
        # 5. Volume conversion (1 mm depth on 1 Hectare = 10,000 Liters)
        volume_liters = net_irr_depth * 10000.0 * farm_size_hectares
        
        return {
            'et0_mm_day': round(et0, 2),
            'etc_mm_day': round(etc, 2),
            'net_irrigation_depth_mm': round(net_irr_depth, 2),
            'irrigation_volume_liters': round(volume_liters, 2)
        }
    except Exception as e:
        print(f"Error calculating irrigation: {e}. Returning default estimation.")
        # Default safety fallback: 5mm/day net loss
        fallback_depth = max(0.0, 5.0 * kc - (precip_mm * 0.8))
        return {
            'et0_mm_day': 5.0,
            'etc_mm_day': round(5.0 * kc, 2),
            'net_irrigation_depth_mm': round(fallback_depth, 2),
            'irrigation_volume_liters': round(fallback_depth * 10000.0 * farm_size_hectares, 2)
        }

if __name__ == "__main__":
    # Test calculation
    print(calculate_irrigation(temp_c=28.0, humidity=65.0, precip_mm=0.0, solar_radiation=15.0, kc=1.15))
