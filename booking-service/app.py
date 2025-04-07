from flask import Flask, request, jsonify, send_from_directory,Response
from kafka import KafkaProducer
import json
import os
import time
from queue import Queue
import mysql.connector 


event_queue = Queue()

app = Flask(__name__)

# Use environment variable or fallback to default
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
TOPIC_NAME = "seat_booking"

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# @app.route('/')
# def index():
#     return send_from_directory('/frontend', 'seat_booking.html')

@app.route('/api/kafka/send', methods=['POST'])
def send_to_kafka():
    data = request.json
    print(f"[Booking-Service] Received seat booking: {data}")  # 👈 Add this line
    producer.send(TOPIC_NAME, data)
    producer.flush()
    print(f"Data sent to Kafka: {data}")  # 👈 Add this line
    return jsonify({"message": "Seat booking request sent!"}), 200

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            if not event_queue.empty():
                message = event_queue.get()
                yield f'data: {message}\n\n'
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")


@app.route('/api/booked-seats', methods=['GET'])
def get_booked_seats():
    connection = mysql.connector.connect(
        host='mysql-db',
        user='root',
        password='vedu',
        database='seat_booking_db'
    )
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT seat_number FROM seats WHERE status = 'booked'")
    seats = cursor.fetchall()
    connection.close()
    
    # Extract just the seat numbers
    booked_seats = [seat['seat_number'] for seat in seats]
    
    return jsonify({"booked_seats": booked_seats})

@app.route("/health")
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
