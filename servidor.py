from flask import Flask

app = Flask(__name__)

@app.route("/")
def pagina_inicial():
    return "Servidor funcionando!"

app.run(debug=True)
