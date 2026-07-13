import requests
#Prueba
'''
Mismos pasos para realizar peticiones a los demas endpoints
/ o  agregar tarea a redis para que cada noche realize el envio a un correo.
'''
# Login para obtener el token
resp = requests.post(
    "http://localhost:8000/api/token/",
    json={"username": "kali", "password": "kali"},
)
access_token = resp.json()["access"]

#  Pedir el reporte
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