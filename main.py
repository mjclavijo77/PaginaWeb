from flask import Flask, render_template, request, jsonify, redirect, url_for
import gestor_datos 

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        
        nuevo_usuario = {
            "correo": request.form.get("correo"),
            "usuario": request.form.get("usuario"),
            "password": request.form.get("password")
        }
        
       
        gestor_datos.guardar_usuario(nuevo_usuario)
        
        
        return redirect(url_for('login'))
        
   
    return render_template("registro.html") 

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/api/buscar")
def buscar_juegos():
    query = request.args.get('q', '').lower()
    
    
    juegos = gestor_datos.cargar_juegos()
    
    if query:
        resultados = [juego for juego in juegos if query in juego['nombre'].lower()]
    else:
        resultados = juegos
        
    return jsonify(resultados)


@app.route("/resultados")
def resultados():
    return render_template("resultados.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)