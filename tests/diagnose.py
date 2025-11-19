#!/usr/bin/env python3
"""
Diagnostic script to check Qdrant and API connectivity.
Load environment from .env file if it exists.
"""
import os
import requests
import socket
from pathlib import Path
from urllib.parse import urlparse

# Load .env file if it exists
env_file = Path(__file__).parent.parent / "app" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

QDRANT_HOST = os.getenv("QDRANT_HOST", "115.190.24.157")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
MODELARK_BASE_URL = "https://ai.gitee.com/v1"

def test_socket_connection(host, port, timeout=5):
    """Test if we can connect to a host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_http_endpoint(url, timeout=5):
    """Test if we can reach an HTTP endpoint."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500
    except Exception as e:
        return False

def main():
    print("=" * 60)
    print("Mem0 Diagnostic Check")
    print("=" * 60)
    
    # Test Qdrant connectivity
    print(f"\n[1] Testing Qdrant Connection")
    print(f"    Host: {QDRANT_HOST}:{QDRANT_PORT}")
    socket_ok = test_socket_connection(QDRANT_HOST, QDRANT_PORT)
    print(f"    Socket: {'✓ OK' if socket_ok else '✗ FAILED'}")
    
    qdrant_url = f"http://{QDRANT_HOST}:{QDRANT_PORT}/health"
    http_ok = test_http_endpoint(qdrant_url)
    print(f"    HTTP /health: {'✓ OK' if http_ok else '✗ FAILED'}")
    
    if not socket_ok:
        print(f"    ⚠ Cannot connect to Qdrant. Check:")
        print(f"      - Is Qdrant running at {QDRANT_HOST}:{QDRANT_PORT}?")
        print(f"      - Is there a firewall blocking the connection?")
        print(f"      - Docker network isolation?")
    
    # Test Zhipu AI API
    print(f"\n[2] Testing Zhipu AI API")
    print(f"    Base URL: {ZHIPU_BASE_URL}")
    zhipu_ok = test_http_endpoint(ZHIPU_BASE_URL)
    print(f"    HTTP Reachable: {'✓ OK' if zhipu_ok else '✗ FAILED'}")
    
    # Test ModelArk API
    print(f"\n[3] Testing ModelArk API")
    print(f"    Base URL: {MODELARK_BASE_URL}")
    modelark_ok = test_http_endpoint(MODELARK_BASE_URL)
    print(f"    HTTP Reachable: {'✓ OK' if modelark_ok else '✗ FAILED'}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Summary:")
    all_ok = socket_ok and http_ok and zhipu_ok and modelark_ok
    if all_ok:
        print("✓ All services are reachable!")
    else:
        print("✗ Some services are not reachable. See details above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
