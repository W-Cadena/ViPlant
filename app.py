from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
import base64
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuración MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1209'
app.config['MYSQL_DB'] = 'datosPlanta'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Ruta para guardar imágenes
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"mensaje": "Hola desde Flask"}), 200

# POST: Recibir datos en formato JSON con imagen base64
@app.route('/api/datos', methods=['POST'])
def insertar_datos():
    try:
        data = request.get_json()

        humedad = float(data['humedad'])
        temperatura = float(data['temperatura'])
        luminosidad = float(data['luminosidad'])
        prediccion = data['prediccion']
        fecha = data.get('fecha', datetime.now().date())
        imagen_base64 = data['imagen']

        # Guardar imagen desde base64
        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        ruta_archivo = os.path.join(UPLOAD_FOLDER, nombre_archivo)

        with open(ruta_archivo, "wb") as f:
            f.write(base64.b64decode(imagen_base64))

        # Insertar en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO datos (fecha, humedad, temperatura, luminosidad, imagen, prediccion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (fecha, humedad, temperatura, luminosidad, nombre_archivo, prediccion))
        mysql.connection.commit()
        cur.close()

        return jsonify({'mensaje': 'Datos guardados correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# GET: Enviar datos a la app móvil
@app.route('/api/datos', methods=['GET'])
def obtener_datos():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM datos ORDER BY id DESC LIMIT 50")
        datos = cur.fetchall()
        cur.close()

        servidor = request.host_url.rstrip('/')
        for item in datos:
            nombre_imagen = item['imagen'].replace('uploads/', '')
            item['imagen'] = f"{servidor}/uploads/{nombre_imagen}"

        return jsonify(datos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Servir imágenes
@app.route('/uploads/<path:nombre>')
def servir_imagen(nombre):
    return send_from_directory(UPLOAD_FOLDER, nombre)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
