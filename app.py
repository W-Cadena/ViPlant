from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Inicializar Firebase
# Cargar el JSON desde variable de entorno
firebase_config_str = os.getenv("FIREBASE_CONFIG_JSON")
firebase_config_dict = json.loads(firebase_config_str.replace("\\n", "\n"))

# Inicializar Firebase con el diccionario
cred = credentials.Certificate(firebase_config_dict)
firebase_admin.initialize_app(cred)

# Inicializar Firestore
db = firestore.client()

# Carpeta donde se guardarán las imágenes
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ruta de prueba
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"mensaje": "Hola desde Flask con Firebase"}), 200

# POST: Recibir datos con imagen base64
@app.route('/api/datos', methods=['POST'])
def insertar_datos():
    try:
        data = request.get_json()

        humedad = float(data['humedad'])
        temperatura = float(data['temperatura'])
        luminosidad = float(data['luminosidad'])
        prediccion = data['prediccion']
        fecha = data.get('fecha', str(datetime.now().date()))
        imagen_base64 = data['imagen']

        # Guardar imagen localmente
        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        ruta_archivo = os.path.join(UPLOAD_FOLDER, nombre_archivo)
        with open(ruta_archivo, "wb") as f:
            f.write(base64.b64decode(imagen_base64))

        # Insertar en Firestore
        db.collection('mediciones').add({
            'fecha': fecha,
            'humedad': humedad,
            'temperatura': temperatura,
            'luminosidad': luminosidad,
            'imagen': nombre_archivo,
            'prediccion': prediccion,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({'mensaje': 'Datos guardados en Firebase correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# GET: Obtener últimos 50 datos
@app.route('/api/datos', methods=['GET'])
def obtener_datos():
    try:
        docs = db.collection('mediciones').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()
        datos = []
        servidor = request.host_url.rstrip('/')

        for doc in docs:
            item = doc.to_dict()
            nombre_imagen = item.get('imagen', '')
            item['imagen'] = f"{servidor}/uploads/{nombre_imagen}"
            datos.append(item)

        return jsonify(datos), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Servir imágenes
@app.route('/uploads/<path:nombre>')
def servir_imagen(nombre):
    return send_from_directory(UPLOAD_FOLDER, nombre)

port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)
