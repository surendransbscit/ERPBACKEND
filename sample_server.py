import eventlet
import eventlet.wsgi
import socketio
import serial
import time
from wsgiref.simple_server import make_server
from socketio import WSGIApp

# Monkey patch for async support
eventlet.monkey_patch()

# Initialize Socket.IO server
sio = socketio.Server(cors_allowed_origins="*")

# Set up the serial port
SERIAL_PORT = "COM1"
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except Exception as e:
    print(f"Error opening serial port: {e}")
    ser = None

# Function to read weight from the serial port
def read_weight():
    if ser and ser.isOpen():
        ser.write(b'P\r\n')
        time.sleep(0.5)
        data = ser.readline().decode().strip()
        return data if data else "No Data"
    return "Error: Serial Port Not Open"

# Background task to send weight updates
def weight_stream():
    while True:
        weight = read_weight()
        print("Weight Data:", weight)
        sio.emit("weight-update", {"weight": weight})
        eventlet.sleep(1)  # Allow async execution

# Function to handle HTTP request (for "Server is running" message)
def simple_app(environ, start_response):
    if environ["PATH_INFO"] == "/":
        status = "200 OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [b"Server is running"]
    else:
        return sio_app(environ, start_response)

# Define Socket.IO events
@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")
    sio.emit("new_estimation_created", {"message": "Hello from server!"}, to=sid)

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
def new_estimation_created(sid, data):
    print(f"Received new_estimation_created event: {data}")
    sio.emit("new_estimation_created", data)

@sio.event
def update_notification():
    print("New notification arrived.")
    sio.emit("update_notification")

@sio.event
def estimation_approved():
    print("Estimation approved.")
    sio.emit("estimation_approved")

# Wrap the Socket.IO app with WSGI
sio_app = WSGIApp(sio, simple_app)

if __name__ == "__main__":
    print("Starting standalone Socket.IO server on port 8001...")
    
    # Start weight streaming in the background
    eventlet.spawn(weight_stream)
    
    # Run the WSGI server with eventlet
    eventlet.wsgi.server(eventlet.listen(("", 8001)), sio_app)
