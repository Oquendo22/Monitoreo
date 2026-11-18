import os
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "monitoreo_industrial"

RANGOS = {
    "temperatura": (-10, 100),
    "presion": (0, 500),
    "vibracion": (0, 5),
}

client = None
sensores = None
conexion_error = None

try:
    if not MONGO_URI:
        raise RuntimeError(
            "Falta configurar MONGO_URI en el archivo .env. "
            "Copia .env.example como .env y pega tu cadena de MongoDB Atlas."
        )
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]
    sensores = db["sensores"]
    print(f"Conectado a MongoDB. Base de datos: {DB_NAME}")
except Exception as exc:
    conexion_error = str(exc)
    print("No fue posible conectar con MongoDB:", conexion_error)


def verificar_conexion():
    global conexion_error
    if client is None:
        return False
    try:
        client.admin.command("ping")
        conexion_error = None
        return True
    except PyMongoError as exc:
        conexion_error = str(exc)
        return False


@app.before_request
def comprobar_db():
    if not verificar_conexion():
        return jsonify({
            "error": "No hay conexión con MongoDB.",
            "detalle": conexion_error or "Verifica MONGO_URI y la configuración de Atlas."
        }), 503


def interpretar_fecha(valor):
    if not isinstance(valor, str):
        return None
    try:
        # Acepta fechas ISO 8601, por ejemplo 2026-11-06T10:30:00
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None


def validar_datos(data, tipo_fijo=None, parcial=False):
    if not isinstance(data, dict):
        return None, "Envía un objeto JSON en el cuerpo de la solicitud."

    tipo = tipo_fijo or data.get("tipo")
    if tipo not in RANGOS:
        return None, "tipo debe ser temperatura, presion o vibracion."

    if tipo_fijo and "tipo" in data and data["tipo"] != tipo_fijo:
        return None, "El tipo no puede cambiar durante la actualización."

    campos = ("valor", "ubicacion", "fecha")
    if not parcial:
        faltantes = [campo for campo in campos if campo not in data]
        if faltantes:
            return None, "Faltan campos obligatorios: " + ", ".join(faltantes)

    resultado = {}

    if "valor" in data:
        valor = data["valor"]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            return None, "valor debe ser numérico."
        minimo, maximo = RANGOS[tipo]
        if not minimo <= valor <= maximo:
            return None, f"Para {tipo}, valor debe estar entre {minimo} y {maximo}."
        resultado["valor"] = valor

    if "ubicacion" in data:
        ubicacion = data["ubicacion"]
        if not isinstance(ubicacion, str) or not ubicacion.strip():
            return None, "ubicacion es obligatoria y debe contener texto."
        resultado["ubicacion"] = ubicacion.strip()

    if "fecha" in data:
        fecha = interpretar_fecha(data["fecha"])
        if fecha is None:
            return None, "fecha debe ser una fecha válida en formato ISO 8601."
        resultado["fecha"] = fecha

    if not resultado:
        return None, "No hay campos válidos para actualizar."

    if tipo_fijo is None:
        resultado["tipo"] = tipo

    return resultado, None


def convertir_sensor(sensor):
    sensor["_id"] = str(sensor["_id"])
    if isinstance(sensor.get("fecha"), datetime):
        sensor["fecha"] = sensor["fecha"].isoformat()
    return sensor


@app.get("/")
def inicio():
    return jsonify({
        "mensaje": "API de Monitoreo Industrial funcionando.",
        "base_de_datos": DB_NAME,
        "coleccion": "sensores",
        "endpoints": {
            "crear": "POST /sensores",
            "consultar_todos": "GET /sensores",
            "filtrar_tipo": "GET /sensores?tipo=temperatura",
            "actualizar_por_tipo": "PUT /sensores/<tipo>",
            "eliminar_por_tipo": "DELETE /sensores/<tipo>"
        }
    }), 200


@app.post("/sensores")
def crear_sensor():
    data = request.get_json(silent=True)
    datos, error = validar_datos(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        resultado = sensores.insert_one(datos)
        return jsonify({
            "mensaje": "Sensor creado correctamente.",
            "id": str(resultado.inserted_id)
        }), 201
    except PyMongoError:
        app.logger.exception("Error al crear sensor")
        return jsonify({"error": "No fue posible guardar el sensor."}), 500


@app.get("/sensores")
def consultar_sensores():
    tipo = request.args.get("tipo")
    if tipo and tipo not in RANGOS:
        return jsonify({"error": "tipo debe ser temperatura, presion o vibracion."}), 400

    try:
        filtro = {"tipo": tipo} if tipo else {}
        resultado = [convertir_sensor(s) for s in sensores.find(filtro)]
        return jsonify(resultado), 200
    except PyMongoError:
        app.logger.exception("Error al consultar sensores")
        return jsonify({"error": "No fue posible consultar los sensores."}), 500


@app.put("/sensores/<tipo>")
def actualizar_por_tipo(tipo):
    if tipo not in RANGOS:
        return jsonify({"error": "Tipo de sensor no válido."}), 400

    data = request.get_json(silent=True)
    datos, error = validar_datos(data, tipo_fijo=tipo, parcial=True)
    if error:
        return jsonify({"error": error}), 400

    try:
        resultado = sensores.update_many({"tipo": tipo}, {"$set": datos})
        return jsonify({
            "mensaje": "Actualización realizada.",
            "sensores_encontrados": resultado.matched_count,
            "sensores_modificados": resultado.modified_count
        }), 200
    except PyMongoError:
        app.logger.exception("Error al actualizar sensores")
        return jsonify({"error": "No fue posible actualizar los sensores."}), 500


@app.delete("/sensores/<tipo>")
def eliminar_por_tipo(tipo):
    if tipo not in RANGOS:
        return jsonify({"error": "Tipo de sensor no válido."}), 400

    try:
        resultado = sensores.delete_many({"tipo": tipo})
        return jsonify({
            "mensaje": "Eliminación realizada.",
            "sensores_eliminados": resultado.deleted_count
        }), 200
    except PyMongoError:
        app.logger.exception("Error al eliminar sensores")
        return jsonify({"error": "No fue posible eliminar los sensores."}), 500


@app.errorhandler(404)
def ruta_no_encontrada(_error):
    return jsonify({"error": "Ruta no encontrada."}), 404


@app.errorhandler(405)
def metodo_no_permitido(_error):
    return jsonify({"error": "Método HTTP no permitido."}), 405


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
