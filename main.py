
import json
import logging
import os

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    flash
)

import gestor_datos
from backend.game_facade import GameCatalogFacade


app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "gamefinder-clave-local"
)
app.config["JSON_AS_ASCII"] = False

logging.basicConfig(level=logging.INFO)

catalogo = GameCatalogFacade()


def obtener_usuario_actual():
    return session.get("correo")


@app.route("/")
def inicio():
    return render_template(
        "index.html",
        usuario=session.get("usuario")
    )


@app.route("/favoritos")
def favoritos():
    correo = obtener_usuario_actual()

    if not correo:
        flash("Debes iniciar sesión para ver tus favoritos.")
        return redirect(url_for("login"))

    return render_template(
        "favoritos.html",
        favoritos=gestor_datos.obtener_favoritos(correo),
        usuario=session.get("usuario", correo)
    )


@app.route("/favoritos/agregar", methods=["POST"])
def agregar_favorito():
    correo = obtener_usuario_actual()

    if not correo:
        flash("Debes iniciar sesión para guardar videojuegos.")
        return redirect(url_for("login"))

    try:
        datos_juego = json.loads(
            request.form.get("juego_json", "{}")
        )
    except (json.JSONDecodeError, TypeError):
        flash("No se pudieron leer los datos del videojuego.")
        return redirect(url_for("inicio"))

    if not isinstance(datos_juego, dict) or not datos_juego.get("nombre"):
        flash("Los datos del videojuego están incompletos.")
        return redirect(url_for("inicio"))

    if gestor_datos.guardar_favorito(correo, datos_juego):
        flash("¡Videojuego agregado a tus favoritos!")
    else:
        flash("Este videojuego ya está en tus favoritos.")

    return redirect(
        url_for("resultados", q=datos_juego["nombre"])
    )


@app.route("/favoritos/eliminar", methods=["POST"])
def quitar_favorito():
    correo = obtener_usuario_actual()

    if not correo:
        flash("Debes iniciar sesión.")
        return redirect(url_for("login"))

    nombre = request.form.get("nombre", "").strip()

    if nombre:
        if gestor_datos.eliminar_favorito(correo, nombre):
            flash("Videojuego eliminado de tus favoritos.")
        else:
            flash("No se encontró ese videojuego en tus favoritos.")

    return redirect(url_for("favoritos"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":

        nuevo_usuario = {
            "correo": request.form.get(
                "correo", ""
            ).strip().lower(),

            "usuario": request.form.get(
                "usuario", ""
            ).strip(),

            "password": request.form.get(
                "password", ""
            )
        }

        confirmar = request.form.get(
            "confirm-password", ""
        )

        if not all(nuevo_usuario.values()):
            return render_template(
                "registro.html",
                error="Debes completar todos los campos."
            )

        if nuevo_usuario["password"] != confirmar:
            return render_template(
                "registro.html",
                error="Las contraseñas no coinciden."
            )

        if len(nuevo_usuario["password"]) < 6:
            return render_template(
                "registro.html",
                error="La contraseña debe tener al menos 6 caracteres."
            )

        try:
            guardado = gestor_datos.guardar_usuario(
                nuevo_usuario
            )

        except OSError:
            app.logger.exception(
                "No se pudo guardar el usuario."
            )

            return render_template(
                "registro.html",
                error=(
                    "No se pudo guardar el registro. "
                    "Revisa los permisos de archivos."
                )
            )

        if not guardado:
            return render_template(
                "registro.html",
                error="Ese correo ya está registrado."
            )

        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        correo = request.form.get(
            "correo", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        usuario = gestor_datos.validar_usuario(
            correo,
            password
        )

        if usuario:
            session.clear()

            session["correo"] = usuario["correo"]
            session["usuario"] = usuario.get(
                "usuario",
                correo
            )

            return redirect(url_for("inicio"))

        return render_template(
            "login.html",
            error="Correo o contraseña incorrectos."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()

    flash("Has cerrado sesión.")

    return redirect(url_for("inicio"))


@app.route("/resultados")
def resultados():
    nombre_juego = request.args.get(
        "q", ""
    ).strip()

    correo = obtener_usuario_actual()

    if not nombre_juego:
        return render_template(
            "resultados.html",
            juego=None,
            error="Debes escribir el nombre de un videojuego.",
            usuario=session.get("usuario"),
            es_favorito=False
        )

    try:
        datos = catalogo.obtener_datos_completos(
            nombre_juego
        )

    except Exception:
        app.logger.exception(
            "Error al consultar las APIs para %s",
            nombre_juego
        )

        return render_template(
            "resultados.html",
            juego=None,
            error=(
                "Ocurrió un problema al consultar los servicios "
                "de videojuegos. Verifica tu conexión, las "
                "dependencias y la configuración de las APIs."
            ),
            usuario=session.get("usuario"),
            es_favorito=False
        )

    if not datos:
        return render_template(
            "resultados.html",
            juego=None,
            error=(
                "No se encontró el videojuego. Comprueba el nombre "
                "o intenta con otro título."
            ),
            usuario=session.get("usuario"),
            es_favorito=False
        )

    es_favorito = (
        gestor_datos.comprobar_favorito(
            correo,
            datos["nombre"]
        )
        if correo else False
    )

    return render_template(
        "resultados.html",
        juego=datos,
        error=None,
        usuario=session.get("usuario"),
        es_favorito=es_favorito
    )


@app.route("/api/buscar")
def buscar_juegos():
    query = request.args.get(
        "q", ""
    ).strip()

    limite = request.args.get(
        "limite",
        6,
        type=int
    )

    limite = min(max(limite, 1), 12)

    if len(query) < 2:
        return jsonify([])

    try:
        juegos = catalogo.buscar_sugerencias(
            query=query,
            limite=limite
        )

        return jsonify(juegos)

    except Exception:
        app.logger.exception(
            "Error al buscar sugerencias."
        )

        return jsonify([]), 500


@app.route("/api/videojuegos")
def api_videojuegos():
    query = request.args.get(
        "q", ""
    ).strip()

    pagina = max(
        request.args.get("pagina", 1, type=int),
        1
    )

    tamano = min(
        max(request.args.get("tamano", 40, type=int), 1),
        40
    )

    try:
        juegos = catalogo.buscar_sugerencias(
            query=query,
            limite=tamano,
            pagina=pagina
        )

        return jsonify({
            "pagina": pagina,
            "cantidad": len(juegos),
            "videojuegos": juegos
        })

    except Exception:
        app.logger.exception(
            "Error al consultar el catálogo de videojuegos."
        )

        return jsonify({
            "pagina": pagina,
            "cantidad": 0,
            "videojuegos": [],
            "error": "No fue posible consultar el catálogo."
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
