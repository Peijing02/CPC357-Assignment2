import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta
import time
import numpy as np

# MongoDB configuration
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["greenhouse"]
collection = db["data"]

# MQTT configuration
mqtt_broker_address = "34.41.126.16"
mqtt_topic = "greenhouse"

def generate_data():
    """Generate 24 hours of greenhouse environmental data with 30-minute intervals"""
    start_time = datetime(2025, 1, 21, 0, 0, 0)
    documents = []
    
    # Base values optimized for greenhouse conditions
    temp = 25.0  # Starting temperature (°C)
    humidity = 75  # Starting humidity (%)
    soil_moisture = 65  # Starting soil moisture (%)
    light_level = 0  # Starting light level (lux)
    co2_level = 800  # Starting CO2 level (ppm)
    
    # Generate data for every 30 minutes (48 points for 24 hours)
    for i in range(48):
        current_time = start_time + timedelta(minutes=30 * i)
        hour = current_time.hour
        
        # Temperature cycle (peaks at 2 PM)
        temp_cycle = 4 * np.sin((hour - 6) * np.pi / 12)
        
        # Light level cycle (follows sun pattern)
        if 6 <= hour <= 18:
            light_cycle = 50000 * np.sin((hour - 6) * np.pi / 12)
        else:
            light_cycle = 0
            
        # CO2 cycle (inverse to light - plants consume CO2 during day)
        co2_cycle = -200 * np.sin((hour - 6) * np.pi / 12)
        
        # Add random variations
        temp_variation = np.random.normal(0, 0.3)
        humidity_variation = np.random.normal(0, 2)
        soil_moisture_variation = np.random.normal(0, 1)
        light_variation = np.random.normal(0, 1000)
        co2_variation = np.random.normal(0, 50)
        
        # Calculate final values with bounds
        final_temp = round(max(min(temp + temp_cycle + temp_variation, 35), 15), 1)
        final_humidity = int(min(max(humidity + humidity_variation, 60), 90))
        final_soil_moisture = int(min(max(soil_moisture + soil_moisture_variation, 50), 80))
        final_light = max(int(light_level + light_cycle + light_variation), 0)
        final_co2 = max(int(co2_level + co2_cycle + co2_variation), 400)
        
        # Create document
        doc = {
            "timestamp": current_time.isoformat(),
            "data": {
                "temperature": final_temp,
                "humidity": final_humidity,
                "soil_moisture": final_soil_moisture,
                "light_level": final_light,
                "co2_level": final_co2
            },
            "formatted_data": (
                f"Timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Temperature: {final_temp}°C, "
                f"Humidity: {final_humidity}%, "
                f"Soil Moisture: {final_soil_moisture}%, "
                f"Light: {final_light} lux, "
                f"CO2: {final_co2} ppm"
            )
        }
        documents.append(doc)
    
    return documents

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected successfully to MQTT broker")
    else:
        print(f"Connection failed with reason code {reason_code}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully")

def send_data():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        print(f"Connecting to MQTT broker at {mqtt_broker_address}")
        client.connect(mqtt_broker_address, 1883, 60)
        client.loop_start()
        
        print("Generating greenhouse environmental data...")
        sample_data = generate_data()
        
        # Clear existing data
        collection.delete_many({})
        print("Cleared existing data from MongoDB")
        
        for doc in sample_data:
            # Add current sending timestamp
            send_timestamp = datetime.now(timezone.utc).isoformat()
            
            # Publish to MQTT with structured data
            print(f"Publishing: {doc['formatted_data']}")
            client.publish(mqtt_topic, doc['formatted_data'])
            
            # Store in MongoDB
            collection.insert_one(doc)
            
            # Delay between messages
            time.sleep(1)
            
        print(f"Successfully processed {len(sample_data)} data points")
            
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected from MQTT broker")

if __name__ == "__main__":
    send_data()