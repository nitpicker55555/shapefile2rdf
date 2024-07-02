from flask import Flask, jsonify, send_from_directory
import json

app = Flask(__name__, static_folder='static/geojson')

# 预加载 GeoJSON 文件
geojson_files = {
    '1': 'geojson1.geojson',
    '2': 'geojson2.geojson',
    '3': 'geojson3.geojson',
    '4': 'geojson4.geojson',
    '5': 'geojson5.geojson'
}
geojson_data = {}

for key, filepath in geojson_files.items():
    with open(app.static_folder + '/' + filepath, 'r') as file:
        geojson_data[key] = json.load(file)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'templates/introcution.html')

@app.route('/geojson/<key>')
def send_geojson(key):
    return jsonify(geojson_data.get(key, {}))

if __name__ == '__main__':
    app.run(debug=True)
