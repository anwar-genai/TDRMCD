#!/usr/bin/env python3
"""
Test Socket.IO functionality
"""

import socketio
import time

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')
    # Test joining a room
    sio.emit('join_chat', {'room': 'test-room'})
    time.sleep(1)
    # Test sending a message
    sio.emit('send_message', {'room': 'test-room', 'message': 'Hello from test client!'})
    time.sleep(1)
    sio.disconnect()

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.event
def receive_message(data):
    print('Received message:', data)

@sio.event
def user_joined(data):
    print('User joined:', data)

@sio.event
def user_left(data):
    print('User left:', data)

if __name__ == "__main__":
    try:
        sio.connect('http://localhost:5000')
        sio.wait()
    except Exception as e:
        print(f"Connection failed: {e}")
