import subprocess
import hashlib
import os
import sys

class LicenseManager:
    def __init__(self, app_config):
        self.config = app_config
        # This salt is the secret sauce. If someone knows this, they can generate keys.
        # Ideally, use PyArmor to obfuscate this file.
        self.SECRET_SALT = "MAKISE_UI_PRO_SALT_2026_BY_HASAN" 

    def get_hardware_id(self):
        """
        Gets a unique ID for the machine. 
        On Windows, we use the Motherboard UUID via WMIC.
        On Linux/Android (Dev), we use a fallback or machine-id.
        """
        try:
            if os.name == 'nt':
                # Windows command to get UUID
                # Output format:
                # UUID
                # E56006E8-....
                cmd = ['wmic', 'csproduct', 'get', 'uuid']
                # Use shell=False for security (no command injection possible)
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                try:
                    output = subprocess.check_output(cmd, startupinfo=si, shell=False).decode()
                    uuid = output.split('\n')[1].strip()
                    if not uuid:
                        return "UNKNOWN-WIN-ID"
                    return uuid
                except subprocess.CalledProcessError:
                    return "UNKNOWN-WIN-ID"
            else:
                # Fallback for Termux/Linux dev
                if os.path.exists("/etc/machine-id"):
                    with open("/etc/machine-id", "r") as f:
                        return f.read().strip()
                return "DEV-ENV-HARDWARE-ID"
        except Exception as e:
            print(f"HWID Error: {e}")
            return "GENERIC-ID-ERROR"

    def generate_key_for_id(self, hardware_id):
        """
        Generates the expected license key for a given Hardware ID.
        Algorithm: SHA256(HardwareID + Salt) -> First 16 chars -> Chunked
        """
        # Normalize ID
        hw_id_clean = hardware_id.strip()
        
        raw_data = f"{hw_id_clean}{self.SECRET_SALT}".encode()
        hashed = hashlib.sha256(raw_data).hexdigest().upper()
        
        # Take first 16 chars and format as XXXX-XXXX-XXXX-XXXX
        # This creates a reasonably short but unique key
        clean_hash = hashed[:16]
        return "-".join([clean_hash[i:i+4] for i in range(0, 16, 4)])

    def validate_license(self, input_key):
        """
        Checks if the input key matches what the key SHOULD be for this PC.
        """
        if not input_key:
            return False
            
        hw_id = self.get_hardware_id()
        expected_key = self.generate_key_for_id(hw_id)
        
        return input_key.strip().upper() == expected_key

    def is_activated(self):
        """Checks if a valid license file exists."""
        # 1. Check for Build-Time Bypass (No License Version)
        if hasattr(sys, '_MEIPASS'):
            bypass_flag = os.path.join(sys._MEIPASS, "no_license.flag")
            if os.path.exists(bypass_flag):
                return True

        # 2. Standard File Check
        lic_path = self.config.get_config_dir() / "license.key"
        if not os.path.exists(lic_path):
            return False
        
        try:
            with open(lic_path, 'r') as f:
                saved_key = f.read().strip()
            return self.validate_license(saved_key)
        except:
            return False

    def save_license(self, key):
        lic_path = self.config.get_config_dir() / "license.key"
        with open(lic_path, 'w') as f:
            f.write(key.strip().upper())

