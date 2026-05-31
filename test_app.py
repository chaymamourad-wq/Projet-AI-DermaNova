import sys, os
sys.path.append(r"c:/Users/asus/Desktop/SKIN_CANCER_APP_AI")
from app import app
with app.test_client() as client:
    resp = client.get('/')
    print('Status:', resp.status_code)
    # Print a snippet of response data
    print('Data snippet:', resp.data[:200])
