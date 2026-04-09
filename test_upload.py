#!/usr/bin/env python3
"""Quick smoke-test for the new /api/sftp-upload endpoint."""
import io, requests, time

BASE = "http://localhost:5000"

# 1. Confirm /api/sftp-upload route exists
t = time.perf_counter()
r = requests.post(
    f"{BASE}/api/sftp-upload",
    data={"saas": "saasN", "remotePath": "/DEV1"},
    files={"file": ("test_drop.txt", io.BytesIO(b"Hello from drag-and-drop test!"), "text/plain")},
    timeout=30
)
ms = (time.perf_counter() - t) * 1000
print(f"Upload status : {r.status_code}  ({ms:.0f}ms)")
try:
    print(f"Response      : {r.json()}")
except Exception:
    print(f"Response body : {r.text[:200]}")

# 2. Verify it now appears in the directory listing
r2 = requests.get(f"{BASE}/api/sftp-directory", params={"saas": "saasN", "path": "/DEV1"}, timeout=30)
names = [e["name"] for e in r2.json().get("entries", [])]
found = "test_drop.txt" in names
print(f"\nFile appears in /DEV1 listing: {'✅ YES' if found else '❌ NO'}")
print(f"All entries in /DEV1: {names}")

