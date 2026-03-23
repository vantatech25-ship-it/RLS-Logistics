import requests
import json

def test_predict():
    url = "http://localhost:8000/predict"
    data = {
        "hub_features": [
            {"load_factor": 0.75, "connectivity": 3, "latitude": -26.2041, "longitude":  28.0473, "congestion_score": 0.51},
            {"load_factor": 0.55, "connectivity": 2, "latitude": -33.9249, "longitude":  18.4241, "congestion_score": 0.39}
        ],
        "edges": [[0, 1]]
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_predict()
