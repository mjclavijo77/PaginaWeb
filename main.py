from flask import Flask, render_template, request, jsonify, redirect, url_for
import gestor_datos
from backend.game_facade import GameCatalogFacade

app = Flask(__name__)
catalogo = GameCatalogFacade()


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nuevo_usuario = {
            "correo": request.form.get("correo"),
            "usuario": request.form.get("usuario"),
            "password": request.form.get("password"),
        }
        gestor_datos.guardar_usuario(nuevo_usuario)
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/resultados")
def resultados():
    nombre_juego = request.args.get("q", "").strip()

    if not nombre_juego:
        return render_template(
            "resultados.html",
            juego=None,
            error="Debes escribir el nombre de un videojuego.",
        )

    datos = catalogo.obtener_datos_completos(nombre_juego)

    if not datos:
        return render_template(
            "resultados.html",
            juego=None,
            error="No se encontro el videojuego. Intenta con otro nombre.",
        )

    return render_template("resultados.html", juego=datos, error=None)


@app.route("/api/buscar")
def buscar_juegos():
    query = request.args.get("q", "").strip()
    limite = request.args.get("limite", 6, type=int)

    if not query:
        return jsonify([])

    return jsonify(catalogo.buscar_sugerencias(query=query, limite=limite))


@app.route("/api/videojuegos")
def api_videojuegos():
    query = request.args.get("q", "").strip()
    pagina = request.args.get("pagina", 1, type=int)
    tamano = request.args.get("tamano", 40, type=int)

    juegos = catalogo.buscar_sugerencias(query=query, limite=tamano, pagina=pagina)
    return jsonify({
        "pagina": pagina,
        "cantidad": len(juegos),
        "videojuegos": juegos,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)