from flask import Flask, jsonify
from kafka import KafkaConsumer
import mysql.connector
import threading
import json
import os
import time

app = Flask(__name__)

# Configs
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
TOPIC_NAME = "seat_booking"
MYSQL_CONFIG = {
    "host": os.environ.get("DATABASE_HOST", "mysql-db"),
    "user": os.environ.get("DATABASE_USER", "root"),
    "password": os.environ.get("DATABASE_PASSWORD", "vedu"),
    "database": os.environ.get("DATABASE_NAME", "seat_booking_db"),
    "port": 3306,
}

def kafka_listener():
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset='earliest',
                group_id='seat_consumer_group',
                value_deserializer=lambda x: json.loads(x.decode("utf-8"))
            )
            print("[Kafka] Consumer connected successfully")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[Kafka Error] Failed to connect after {max_retries} attempts: {str(e)}")
                return
            print(f"[Kafka] Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    print("[Kafka] Consumer listening...")

    for message in consumer:
        seat_data = message.value.get("seats", [])
        print(f"[Kafka] Received seat data: {seat_data}")
        if seat_data:
            update_seats_in_db(seat_data)

def check_tables_exist(cursor):
    cursor.execute("SHOW TABLES LIKE 'seats'")
    if not cursor.fetchone():
        raise Exception("Seats table does not exist")

def update_seats_in_db(seat_numbers):
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # Verify tables exist
        check_tables_exist(cursor)
        
        print(f"Updating seat status in DB: {seat_numbers}")
        
        # Check seat existence before updating
        for seat in seat_numbers:
            cursor.execute("SELECT 1 FROM seats WHERE seat_number = %s", (seat,))
            if not cursor.fetchone():
                print(f"[MySQL Warning] Seat {seat} does not exist in database")
                continue
                
            cursor.execute(
                "UPDATE seats SET status = 'booked' WHERE seat_number = %s",
                (seat,)
            )
            print(f"[MySQL] Successfully booked seat: {seat}")
            
        connection.commit()
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"[MySQL Error] {err}")
    except Exception as e:
        print(f"[System Error] {str(e)}")

@app.route('/health')
def health():
    return jsonify({"status": "Consumer running"}), 200

@app.route('/api/booked-seats', methods=['GET'])
def get_booked_seats():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT seat_number FROM seats WHERE status = 'booked'")
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        booked_seats = [seat[0] for seat in results]
        return jsonify(booked_seats)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# Start Kafka in background
threading.Thread(target=kafka_listener, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
