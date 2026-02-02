#!/bin/python

import requests
import json
import hashlib
import base64
import os
from bs4 import BeautifulSoup
from Crypto.Cipher import AES

# Configuration
DOC_URL = "https://www.npoint.io/docs/xxxxxx"
PATCH_URL = "https://www.npoint.io/documents/xxxxx"
API_URL = "https://api.npoint.io/xxxxxxxxx"
PASSPHRASE = ""

# Local Data to Add/Merge
NEW_DATA = {
    "users":
}


def derive_key(passphrase):
    return hashlib.sha256(passphrase.encode('utf-8')).digest()

def encrypt_data(data, key):
    json_str = json.dumps(data)
    iv = os.urandom(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(json_str.encode('utf-8'))
    # Format: IV (12) + Ciphertext + Tag (16)
    payload = iv + ciphertext + tag
    return base64.b64encode(payload).decode('utf-8')

def decrypt_data(b64_payload, key):
    try:
        raw = base64.b64decode(b64_payload)
        iv = raw[:12]
        tag = raw[-16:]
        ciphertext = raw[12:-16]
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        print(f"Decryption failed (might be empty or different key): {e}")
        return {"users": []}

def main():
    session = requests.Session()
    key = derive_key(PASSPHRASE)

    # 1. Fetch CSRF
    print("🔥 Fetching CSRF Token...")
    resp = session.get(DOC_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]
    print("✅ CSRF Acquired")

    # 2. Fetch Existing Data
    print("📥 Fetching current data from npoint...")
    try:
        current_resp = requests.get(API_URL)
        if current_resp.status_code == 200:
            remote_json = current_resp.json()
            # Expecting structure: {"data": "BASE64_STRING"}
            if "data" in remote_json:
                print("🔓 Decrypting remote data...")
                current_data = decrypt_data(remote_json["data"], key)
            else:
                print("⚠️ Remote data format unknown, starting fresh.")
                current_data = {"users": []}
        else:
            print("⚠️ Could not fetch remote data, starting fresh.")
            current_data = {"users": []}
    except Exception as e:
        print(f"⚠️ Error fetching: {e}, starting fresh.")
        current_data = {"users": []}

    # 3. Merge Data
    # Simple merge: Add new users if ID not present
    existing_ids = {u["id"] for u in current_data["users"]}
    for user in NEW_DATA["users"]:
        if user["id"] not in existing_ids:
            current_data["users"].append(user)
            print(f"➕ Added user ID {user['id']}")
        else:
            # Update existing?
            for i, u in enumerate(current_data["users"]):
                if u["id"] == user["id"]:
                    current_data["users"][i] = user
                    print(f"🔄 Updated user ID {user['id']}")

    # 4. Encrypt
    print("Cx Encrypting merged data...")
    encrypted_b64 = encrypt_data(current_data, key)
    
    # 5. Prepare Payload
    # npoint structure
    final_json = {"data": encrypted_b64}
    payload_str = json.dumps(final_json)
    
    upload_payload = {
        "contents": payload_str,
        "original_contents": payload_str, # Just to satisfy npoint logic
        "schema": None,
        "original_schema": ""
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "x-csrf-token": csrf_token,
        "origin": "https://www.npoint.io",
        "referer": DOC_URL,
        "user-agent": "Mozilla/5.0"
    }

    # 6. Push
    print("🚀 Pushing to npoint...")
    patch = session.patch(PATCH_URL, headers=headers, data=json.dumps(upload_payload))
    
    if patch.status_code == 200:
        print("✅ Success! Data updated.")
        print(f"API URL: {API_URL}")
    else:
        print(f"❌ Failed: {patch.status_code}")
        print(patch.text)

if __name__ == "__main__":
    main()
