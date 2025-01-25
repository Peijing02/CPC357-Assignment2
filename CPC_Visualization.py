import pymongo
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy import stats

# MongoDB configuration
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["greenhouse"]
collection = db["data"]

def calculate_moving_average(data, window=3):
    """Calculate moving average for smoothing data trends."""
    return np.convolve(data, np.ones(window)/window, mode='valid')

def predict_trend(x, y):
    """Perform linear regression to predict future trend."""
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope, intercept, r_value**2

def generate_trend_narrative(parameter, slope, r2):
    """Generate a narrative description of the trend"""
    trend_descriptions = {
        'temperature': {
            'increasing': "Temperature is steadily rising, indicating heat accumulation.",
            'decreasing': "Temperature is declining, suggesting cooling or external climate influences.",
            'stable': "Temperature remains relatively constant."
        },
        'humidity': {
            'increasing': "Humidity is gradually increasing, potentially indicating higher moisture content.",
            'decreasing': "Humidity is decreasing, making the environment drier.",
            'stable': "Humidity remains consistent."
        },
        'soil_moisture': {
            'increasing': "Soil moisture is increasing, possibly due to irrigation or environmental changes.",
            'decreasing': "Soil moisture is decreasing, which might require attention to plant hydration.",
            'stable': "Soil moisture remains steady."
        },
        'light_level': {
            'increasing': "Light intensity is continuously increasing, reflecting changing daylight.",
            'decreasing': "Light intensity is diminishing, possibly due to cloud cover or time of day.",
            'stable': "Light intensity remains constant."
        },
        'co2_level': {
            'increasing': "CO2 concentration is rising, potentially indicating ventilation issues.",
            'decreasing': "CO2 concentration is dropping, suggesting good ventilation or plant photosynthesis.",
            'stable': "CO2 levels remain relatively stable."
        }
    }

    # Determine trend direction
    if abs(slope) < 0.01:
        trend = 'stable'
    elif slope > 0:
        trend = 'increasing'
    else:
        trend = 'decreasing'

    # Add confidence note based on R²
    confidence_note = "Trend analysis is highly reliable" if r2 > 0.7 else "Trend analysis should be interpreted cautiously"

    return f"{trend_descriptions[parameter][trend]} {confidence_note}, statistical fit R² = {r2:.2f}."

def create_visualization():
    # Initialize lists to store data
    timestamps = []
    temperatures = []
    humidities = []
    soil_moistures = []
    light_levels = []
    co2_levels = []

    try:
        # Fetch all documents from MongoDB
        documents = collection.find()
        
        # Process each document
        for doc in documents:
            if 'data' in doc:
                # Extract timestamp
                timestamp_str = doc['timestamp']
                dt = datetime.fromisoformat(timestamp_str)
                time_only = dt.strftime('%H:%M')
                timestamps.append(time_only)
                
                # Extract sensor data
                data = doc['data']
                temperatures.append(data['temperature'])
                humidities.append(data['humidity'])
                soil_moistures.append(data['soil_moisture'])
                light_levels.append(data['light_level'])
                co2_levels.append(data['co2_level'])

        if timestamps:
            # Convert timestamps to numeric for trend analysis
            x = np.arange(len(timestamps))

            # Create subplots with increased height
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Greenhouse Environmental Monitoring Dashboard', fontsize=16)

            # Temperature and Humidity Plot with Trend
            temp_ma = calculate_moving_average(temperatures)
            hum_ma = calculate_moving_average(humidities)
            
            ax1.plot(timestamps, temperatures, 'r-', label='Temperature (°C)')
            ax1.plot(timestamps[len(timestamps)-len(temp_ma):], temp_ma, 'r--', label='Temp Moving Avg')
            
            ax1_twin = ax1.twinx()
            ax1_twin.plot(timestamps, humidities, 'b-', label='Humidity (%)')
            ax1_twin.plot(timestamps[len(timestamps)-len(hum_ma):], hum_ma, 'b--', label='Humidity Moving Avg')
            
            # Temperature Trend Prediction
            temp_slope, temp_intercept, temp_r2 = predict_trend(x, temperatures)
            pred_temp = temp_slope * x + temp_intercept
            ax1.plot(timestamps, pred_temp, 'r:', label=f'Temp Trend (R²={temp_r2:.2f})')

            ax1.set_title('Temperature and Humidity Trends')
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Temperature (°C)', color='r')
            ax1_twin.set_ylabel('Humidity (%)', color='b')
            
            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax1_twin.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize='small')

            # Soil Moisture Plot with Trend
            soil_ma = calculate_moving_average(soil_moistures)
            soil_slope, soil_intercept, soil_r2 = predict_trend(x, soil_moistures)
            pred_soil = soil_slope * x + soil_intercept
            
            ax2.plot(timestamps, soil_moistures, 'g-', label='Soil Moisture (%)')
            ax2.plot(timestamps[len(timestamps)-len(soil_ma):], soil_ma, 'g--', label='Moisture Moving Avg')
            ax2.plot(timestamps, pred_soil, 'g:', label=f'Moisture Trend (R²={soil_r2:.2f})')
            ax2.set_title('Soil Moisture Trends')
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Moisture (%)')
            ax2.legend(fontsize='small')

            # Light Level Plot with Trend
            light_ma = calculate_moving_average(light_levels)
            light_slope, light_intercept, light_r2 = predict_trend(x, light_levels)
            pred_light = light_slope * x + light_intercept
            
            ax3.plot(timestamps, light_levels, 'y-', label='Light (lux)')
            ax3.plot(timestamps[len(timestamps)-len(light_ma):], light_ma, 'y--', label='Light Moving Avg')
            ax3.plot(timestamps, pred_light, 'y:', label=f'Light Trend (R²={light_r2:.2f})')
            ax3.set_title('Light Level Trends')
            ax3.set_xlabel('Time')
            ax3.set_ylabel('Light (lux)')
            ax3.legend(fontsize='small')

            # CO2 Level Plot with Trend
            co2_ma = calculate_moving_average(co2_levels)
            co2_slope, co2_intercept, co2_r2 = predict_trend(x, co2_levels)
            pred_co2 = co2_slope * x + co2_intercept
            
            ax4.plot(timestamps, co2_levels, 'm-', label='CO2 (ppm)')
            ax4.plot(timestamps[len(timestamps)-len(co2_ma):], co2_ma, 'm--', label='CO2 Moving Avg')
            ax4.plot(timestamps, pred_co2, 'm:', label=f'CO2 Trend (R²={co2_r2:.2f})')
            ax4.set_title('CO2 Level Trends')
            ax4.set_xlabel('Time')
            ax4.set_ylabel('CO2 (ppm)')
            ax4.legend(fontsize='small')

            # Rotate x-axis labels
            for ax in [ax1, ax2, ax3, ax4]:
                ax.tick_params(axis='x', rotation=45)

            plt.tight_layout()
            plt.show()
            
            trend_narratives = {
                'temperature': generate_trend_narrative('temperature', temp_slope, temp_r2),
                'humidity': generate_trend_narrative('humidity', 0, 0),
                'soil_moisture': generate_trend_narrative('soil_moisture', soil_slope, soil_r2),
                'light_level': generate_trend_narrative('light_level', light_slope, light_r2),
                'co2_level': generate_trend_narrative('co2_level', co2_slope, co2_r2)
            }

            # Print narrative summaries
            print("\nGreenhouse Environment Trend Analysis:")
            for parameter, narrative in trend_narratives.items():
                print(f"{parameter.capitalize()} Trend: {narrative}")
                
        else:
            print("No data found to plot")

    except pymongo.errors.ConnectionError:
        print("Error: Could not connect to MongoDB")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    create_visualization()