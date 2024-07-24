from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sqlite3
import cv2
import time
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Ensure the static directory exists

if not os.path.exists('static'):
    os.makedirs('static')

# Initialize SQL database

def init_db():
    conn = sqlite3.connect('mouse_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouse_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x INTEGER,
            y INTEGER,
            image_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to save mouse coordinates and image path to database

def save_to_db(x, y, image_path):
    conn = sqlite3.connect('mouse_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO mouse_data (x, y, image_path) VALUES (?, ?, ?)', (x, y, image_path))
    conn.commit()
    conn.close()

# Function to capture an image from the webcam

def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        timestamp = int(time.time())
        image_filename = f'capture_{timestamp}.jpg'
        image_path = os.path.join('static', image_filename)
        cv2.imwrite(image_path, frame)
        cap.release()
        return image_filename
    cap.release()
    return None

# Route to serve the web page

@app.route('/')
def index():
    return render_template('index.html')

# Routee to fetch mouse coordinates and images

@app.route('/data')
def fetch_data():
    conn = sqlite3.connect('mouse_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM mouse_data')
    rows = cursor.fetchall()
    conn.close()
    return render_template('data.html', rows=rows)

# WebSocket to handle mouse movements

@socketio.on('mouse_move')
def handle_mouse_move(data):
    x = data['x']
    y = data['y']
    print(f'Mouse moved to: ({x}, {y})')

# WebSocket to handle mouse click

@socketio.on('mouse_click')
def handle_mouse_click(data):
    x = data['x']
    y = data['y']
    print(f'Mouse clicked at: ({x}, {y})')
    image_filename = capture_image()
    if image_filename:
        save_to_db(x, y, image_filename)
        emit('image_captured', {'image_path': f'/static/{image_filename}'})

# Check name
if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
