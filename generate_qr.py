import requests
import os

url = "https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=http://192.168.0.116:5000/dashboard"
output_path = r"C:\Users\IVAN\.gemini\antigravity\brain\9203cd17-fe55-48b4-9c36-4b6343eb7626\rls_mobile_qr.png"

try:
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"QR Code saved to {output_path}")
    else:
        print(f"Failed to download QR code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
