import hashlib
import os
import subprocess
import sys

# The secret salt must match core/licensing.py
SECRET_SALT = "MAKISE_UI_PRO_SALT_2026_BY_HASAN"

def get_hardware_id():
    """
    Duplicate logic from core/licensing.py to get the current machine's hardware ID.
    """
    try:
        if os.name == 'nt':
            cmd = ['wmic', 'csproduct', 'get', 'uuid']
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            try:
                output = subprocess.check_output(cmd, startupinfo=si, shell=False).decode()
                uuid = output.split('\n')[1].strip()
                if not uuid:
                    return "UNKNOWN-WIN-ID"
                return uuid
            except Exception:
                return "UNKNOWN-WIN-ID"
        else:
            if os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            return "DEV-ENV-HARDWARE-ID"
    except Exception as e:
        return f"ERROR-{e}"

def generate_key_for_id(hardware_id):
    """
    Algorithm: SHA256(HardwareID + Salt) -> First 16 chars -> Chunked
    """
    hw_id_clean = hardware_id.strip()
    raw_data = f"{hw_id_clean}{SECRET_SALT}".encode()
    hashed = hashlib.sha256(raw_data).hexdigest().upper()
    
    clean_hash = hashed[:16]
    return "-".join([clean_hash[i:i+4] for i in range(0, 16, 4)])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Generate for a provided ID
        hw_id = sys.argv[1]
        print(f"Generating key for provided ID: {hw_id}")
    else:
        # Generate for this machine
        hw_id = get_hardware_id()
        print(f"Current Machine Hardware ID: {hw_id}")

    key = generate_key_for_id(hw_id)
    print(f"\nYour License Key is:\n{key}\n")
    print("Save this key to a file named 'license.key' in the config directory or paste it into the activation dialog.")
