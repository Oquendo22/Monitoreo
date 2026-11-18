# MonitoreoIndustrialAPI

API REST para registrar y administrar sensores industriales con Python, Flask y MongoDB Atlas.

## 1. Requisitos

- Python 3.10 o superior.
- Una cuenta y un clúster en MongoDB Atlas.
- Postman (para probar los endpoints).
- Visual Studio Code (recomendado).

## 2. Preparar MongoDB Atlas

1. En Atlas, crea la base de datos `monitoreo_industrial` y la colección `sensores` (si aún no existen).
2. En **Database Access**, crea un usuario de base de datos y guarda su contraseña.
3. En **Network Access**, permite la dirección IP desde la que te conectas. Para una práctica, puedes agregar tu IP actual.
4. En el clúster, pulsa **Connect > Drivers**, selecciona Python y copia la cadena de conexión.
5. Copia `.env.example` y renombra la copia como `.env`.
6. Pega la cadena en `MONGO_URI` y reemplaza los datos de ejemplo. No compartas el archivo `.env`.

La base de datos y la colección también pueden crearse automáticamente al insertar el primer documento, si no existen.

## 3. Instalar y ejecutar en Windows

Abre la carpeta del proyecto en VS Code y ejecuta en la terminal:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La API quedará disponible en `http://127.0.0.1:5000`.

Abre esa dirección en el navegador para comprobar que la API responde.

## 4. Endpoints

| Método | Dirección | Función |
|---|---|---|
| POST | `/sensores` | Crea un sensor |
| GET | `/sensores` | Consulta todos los sensores |
| GET | `/sensores?tipo=temperatura` | Filtra por tipo |
| PUT | `/sensores/temperatura` | Actualiza los sensores de ese tipo |
| DELETE | `/sensores/temperatura` | Elimina los sensores de ese tipo |

Tipos permitidos: `temperatura`, `presion`, `vibracion`.

Rangos:
- Temperatura: -10 a 100 °C.
- Presión: 0 a 500 kPa.
- Vibración: 0 a 5 mm/s.

## 5. Ejemplo POST en Postman

- Método: `POST`
- URL: `http://127.0.0.1:5000/sensores`
- En **Body > raw > JSON**, enviar:

```json
{
  "tipo": "temperatura",
  "valor": 35.5,
  "ubicacion": "Planta principal",
  "fecha": "2026-11-06T10:30:00"
}
```

Para filtrar, usar `GET http://127.0.0.1:5000/sensores?tipo=temperatura`.

Para actualizar por tipo, usar `PUT http://127.0.0.1:5000/sensores/temperatura` con:

```json
{
  "valor": 40,
  "ubicacion": "Planta secundaria",
  "fecha": "2026-11-06T12:00:00"
}
```

Para eliminar por tipo, usar `DELETE http://127.0.0.1:5000/sensores/temperatura`.

**Atención:** PUT y DELETE trabajan sobre todos los documentos del tipo indicado, según el enunciado de la actividad. DELETE elimina permanentemente esos documentos.

## 6. Códigos de respuesta

- `200`: consulta, actualización o eliminación correcta.
- `201`: sensor creado.
- `400`: datos inválidos.
- `404`: ruta inexistente.
- `405`: método HTTP no permitido.
- `500`: error interno al operar con MongoDB.
- `503`: no hay conexión con MongoDB.

## 7. Evidencias para la entrega

Tomar capturas reales de:
1. La base de datos y colección en MongoDB Atlas.
2. La API ejecutándose en VS Code.
3. POST exitoso.
4. GET de todos los sensores.
5. GET filtrado por tipo.
6. PUT exitoso.
7. DELETE exitoso.
8. Una validación rechazada (por ejemplo, temperatura 150).

## 8. Seguridad

No subir ni compartir el archivo `.env`, ya que contiene las credenciales de MongoDB. El archivo `.gitignore` excluye ese archivo del control de versiones.
