import eventlet
import eventlet.wsgi
import socketio
from wsgiref.simple_server import make_server
from socketio import WSGIApp

# Initialize Socket.IO server
sio = socketio.Server(cors_allowed_origins="*")

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

# Start the server on port 8001
if __name__ == "__main__":
    print("Starting standalone Socket.IO server on port 8001...")
    eventlet.wsgi.server(eventlet.listen(("", 8001)), sio_app)
