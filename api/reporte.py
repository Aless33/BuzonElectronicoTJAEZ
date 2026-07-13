import requests

# 1. Login para obtener el token
resp = requests.post(
    "http://localhost:8000/api/token/",
    json={"username": "kali", "password": "kali"},
)
access_token = resp.json()["access"]

# 2. Pedir el reporte
resp = requests.get(
    "http://localhost:8000/api/reportes/depositos-diarios/",
    params={"fecha": "2026-07-13"},
    headers={"Authorization": f"Bearer {access_token}"},
)

if resp.status_code == 200:
    with open("reporte.xlsx", "wb") as f:
        f.write(resp.content)
    print("Reporte guardado.")
else:
    print("Error:", resp.status_code, resp.json())