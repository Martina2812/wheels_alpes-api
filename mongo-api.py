from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = MongoClient(os.environ["MONGO_URI"])
db = client[os.environ["MONGO_DB"]]


@app.get("/")
def inicio():
    return {"estado": "API funcionando correctamente"}


# REQUERIMIENTOS DEL PASAJERO

# RF1
@app.post("/resenas")
def post_resena(datos: dict):
    if datos["calificacion"] < 1 or datos["calificacion"] > 5:
        return {"error": "La calificacion debe ser de 1 a 5"}
    
    ya_existe = db.resenas.find_one(
        {"id_viaje": datos["id_viaje"],
         "documento_pasajero": datos["documento_pasajero"]})
    if ya_existe:
        return {"error": "Ya reseñaste este viaje"}
    
    {
        "id_viaje": datos["id_viaje"],
        "documento_conductor": datos["documento_conductor"],
        "nombre_conductor": datos["nombre_conductor"],
        "universidad_conductor": datos["universidad_conductor"],
        "localidad_origen": datos["localidad_origen"],
        "documento_pasajero": datos["documento_pasajero"],
        "nombre_pasajero": datos["nombre_pasajero"],
        "calificacion": datos["calificacion"],
        "comentario": datos["comentario"],
        "estado": "publicada",
        "destacada": False,
        "fecha_creacion": datetime.now(),
        "fecha_edicion": None,
        "respuesta": None,
        "eliminado": None
    }
    
    db.resenas.insert_one(resena)
    return {"mensaje": "Reseña guardada"}


# RF2
@app.put("/resenas/{id_viaje}/{documento_pasajero}")
def put_resena(id_viaje: int, documento_pasajero: str, datos: dict):
    filtro = {"id_viaje": id_viaje, "documento_pasajero": documento_pasajero}
    
    resena = db.resenas.find_one(filtro)
    
    if resena is None:
        return {"error": "Reseña no encontrada"}
    if resena["estado"] == "eliminada":
        return {"error": "La reseña fue eliminada"}
    
    db.resenas.update_one(
        filtro, {
            "$set": {
                "calificacion": datos["calificacion"],
                "comentario": datos["comentario"],
                "fecha_edicion": datetime.now()
                }})
    
    return {"mensaje": "Reseña editada"}


# RF3
@app.delete("/resenas/{id_viaje}/{documento_pasajero}")
def delete_resena(id_viaje: int, documento_pasajero: str):
    filtro = {"id_viaje": id_viaje, "documento_pasajero": documento_pasajero}
   
    db.resenas.update_one(
        filtro, {
            "$set": {
                "estado": "eliminada",
                "eliminado": {"por": "pasajero",
                "fecha": datetime.now()
                }}})
    
    return {"mensaje": "Reseña eliminada"}


# RF4 
@app.get("/conductores/{documento}/resenas")
def get_resenas_conductor(documento: str, orden: str = "fecha", pagina: int = 1):
    campo = "fecha_creacion"
    if orden == "calificacion":
        campo = "calificacion"
        
    resenas = db.resenas.find(
        {"documento_conductor": documento, 
         "estado": "publicada"}, 
        {"_id": 0}
        ).sort(campo, -1).skip((pagina - 1) * 10).limit(10)
    
    return list(resenas)


# RF5 
@app.get("/pasajeros/{documento}/resenas")
def get_historial_pasajero(documento: str):
    
    return list(db.resenas.find(
        {"documento_pasajero": documento}, 
        {"_id": 0})
                )


# REQUERIMIENTOS DEL CONDUCTOR

# RF6 
@app.post("/calificaciones")
def post_calificacion(datos: dict):
    if datos["calificacion"] < 1 or datos["calificacion"] > 5:
        return {"error": "La calificacion debe ser de 1 a 5"}
    
    ya_existe = db.calificaciones_pasajero.find_one(
        {"id_viaje": datos["id_viaje"], 
         "documento_pasajero": datos["documento_pasajero"]})
    
    if ya_existe:
        return {"error": "Ya calificaste a este pasajero en este viaje"}
    
    calificacion = {
        "id_viaje": datos["id_viaje"],
        "documento_conductor": datos["documento_conductor"],
        "nombre_conductor": datos["nombre_conductor"],
        "documento_pasajero": datos["documento_pasajero"],
        "nombre_pasajero": datos["nombre_pasajero"],
        "calificacion": datos["calificacion"],
        "comentario": datos.get("comentario"),
        "fecha_creacion": datetime.now()
    }
    
    db.calificaciones_pasajero.insert_one(calificacion)
    return {"mensaje": "Calificación guardada"}


# RF7 
@app.put("/resenas/{id_viaje}/{documento_pasajero}/respuesta")
def put_respuesta(id_viaje: int, documento_pasajero: str, datos: dict):
    filtro = {"id_viaje": id_viaje, "documento_pasajero": documento_pasajero}
    resena = db.resenas.find_one(filtro)
    
    if resena is None:
        return {"error": "Reseña no encontrada"}
    
    respuesta = {"texto": datos["texto"],
                 "fecha_respuesta": datetime.now(),
                 "fecha_edicion": None}
    
    if resena["respuesta"] is not None:
        respuesta["fecha_respuesta"] = resena["respuesta"]["fecha_respuesta"]
        respuesta["fecha_edicion"] = datetime.now()
    
    db.resenas.update_one(
        filtro, {
            "$set": {
                "respuesta": respuesta
                }})
    
    return {"mensaje": "Respuesta guardada"}


# RF8 
@app.put("/resenas/{id_viaje}/{documento_pasajero}/eliminar")
def put_eliminar_conductor(id_viaje: int, documento_pasajero: str, datos: dict):
    filtro = {"id_viaje": id_viaje, "documento_pasajero": documento_pasajero}
    
    db.resenas.update_one(
        filtro, {
            "$set": {
                "estado": "eliminada", 
                "eliminado": {"por": "conductor", 
                              "motivo": datos.get("motivo"),
                              "fecha": datetime.now()
                              }}})
    
    return {"mensaje": "Reseña eliminada"}


# RF9 
@app.get("/conductores/{documento}/resenas-recibidas")
def get_resenas_recibidas(documento: str, orden: str = "fecha"):
    campo = "fecha_creacion"
    if orden == "calificacion":
        campo = "calificacion"
    
    return list(db.resenas.find(
        {"documento_conductor": documento}, 
        {"_id": 0}
        ).sort(campo, -1))


#TODO: REQUERIMIENTOS FUNCIONALES DE CONSULTA Y DE ANALITICA
