from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)


def cargar_juegos():
    with open('juegos.json', 'r', encoding='utf-8') as archivo:
        return json.load(archivo)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/api/buscar")
def buscar_juegos():
    
    query = request.args.get('q', '').lower()
    juegos = cargar_juegos()
    
    if query:
        
        resultados = [juego for juego in juegos if query in juego['nombre'].lower()]
    else:
        
        resultados = juegos
        
    return jsonify(resultados)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)