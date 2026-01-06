import requests
import re
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from bs4 import BeautifulSoup

class PhoneScraper:
    def __init__(self):
        self.imei_api_url = "https://alpha.imeicheck.com/api/free_with_key/modelBrandName"
        self.imei_api_key = "FB6E-37C8-7D0A-ED31-B48A-12QK"
        self.gsm_search_url = "https://m.gsmarena.com/resl.php3"

    def fetch_details(self, imei):
        """
        Full pipeline: IMEI -> Model Code -> GSMArena Search -> Decrypt -> Phone Name
        """
        try:
            # 1. Get Model Code from IMEI API
            model_code = self._get_model_code_from_imei(imei)
            if not model_code:
                return {"error": "Could not fetch Model Code from IMEI"}

            # 2. Search GSMArena
            return self._search_gsmarena(model_code)

        except Exception as e:
            return {"error": str(e)}

    def _get_model_code_from_imei(self, imei):
        params = {
            "key": self.imei_api_key,
            "imei": imei,
            "format": "json"
        }
        try:
            resp = requests.get(self.imei_api_url, params=params, timeout=10)
            data = resp.json()
            if data.get("status") == "succes": # Note typo in API "succes"
                # Prefer "model" (e.g. 24090RA29I), fallback to "name"
                obj = data.get("object", {})
                return obj.get("model") or obj.get("name")
            return None
        except:
            return None

    def _search_gsmarena(self, query):
        params = {"sSearch": query}
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
            }
            resp = requests.get(self.gsm_search_url, params=params, headers=headers, timeout=10)
            html = resp.text
            
            # 3. Extract Keys and Data
            # Regex to find const KEY = "...", IV = "...", DATA = "..."
            key_match = re.search(r'const\s+KEY\s*=\s*"([^"]+)"', html)
            iv_match  = re.search(r'const\s+IV\s*=\s*"([^"]+)"', html)
            data_match = re.search(r'const\s+DATA\s*=\s*"([^"]+)"', html)

            if not (key_match and iv_match and data_match):
                # Maybe no results or different format?
                # Check for direct results (sometimes not encrypted if direct match?)
                # Actually user specified encrypted format, so assume that.
                return {"model_code": query, "name": f"{query} (No GSMArena match)"}

            key_b64 = key_match.group(1)
            iv_b64 = iv_match.group(1)
            data_b64 = data_match.group(1)

            # 4. Decrypt
            decrypted_html = self._decrypt_aes(key_b64, iv_b64, data_b64)
            
            # 5. Parse HTML to get name
            soup = BeautifulSoup(decrypted_html, 'html.parser')
            # Look for first phone link
            # Structure: <a href="..."><span><img ...></span><strong>NAME</strong></a>
            
            # Try to find 'latest-container' or 'reviews-container' or just the first anchor
            first_match = soup.find('a')
            if first_match:
                strong = first_match.find('strong')
                if strong:
                    full_name = strong.get_text().strip()
                    # Remove region if needed e.g. " (India)"
                    # full_name = re.sub(r'\s*\(.*?\)', '', full_name) 
                    return {"model_code": query, "name": full_name}
            
            return {"model_code": query, "name": f"{query} (Unknown)"}

        except Exception as e:
            print(f"Scrape Error: {e}")
            return {"model_code": query, "name": f"{query} (Scrape Error)"}

    def _decrypt_aes(self, key_b64, iv_b64, data_b64):
        key = base64.b64decode(key_b64)
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(data_b64)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext.decode('utf-8')

if __name__ == "__main__":
    # Test
    s = PhoneScraper()
    # Test with the example IMEI from user prompt (randomly generated or from their example)
    # Using the model name directly for test if no valid IMEI handy
    print("Testing GSMArena Scraper...")
    res = s._search_gsmarena("24090RA29I")
    print(res)
