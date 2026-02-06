
import socket

host = "152.67.159.164"
ports = [5432, 6543, 8000]

def check_port(host, port):
    print(f"Checking {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        result = s.connect_ex((host, port))
        if result == 0:
            print(f"✅ Port {port} is OPEN on {host}")
        else:
            print(f"❌ Port {port} is CLOSED on {host} (Code: {result})")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        s.close()

for port in ports:
    check_port(host, port)
