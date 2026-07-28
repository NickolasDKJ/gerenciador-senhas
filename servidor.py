from flask import Flask, jsonify, request

app = Flask(__name__)

# DADOS FALSOS (vamos simular um banco de dados)
# Isso é uma lista de dicionários - igual ao seu cofre!
senhas_falsas = [
    {"site": "google.com", "usuario": "nickolas@gmail.com", "senha": "senha123"},
    {"site": "github.com", "usuario": "NickolasDKJ", "senha": "git456"},
    {"site": "facebook.com", "usuario": "nickolas.ferreira", "senha": "face789"},
    {"site": "instagram.com", "usuario": "nick_insta", "senha": "insta456"},
    {"site": "x.com", "usuario": "nick_x", "senha": "x123"},
]

# ROTA 1: Página inicial (já existia)
@app.route("/")
def pagina_inicial():
    return "Servidor funcionando! Acesse /senhas para ver os dados em JSON."

# ROTA 2: Retorna as senhas em JSON (NOVA!)
@app.route("/senhas")
def listar_senhas():
    return jsonify (senhas_falsas) # Transforma a lista em JSON

# Teste Rota 2.5 Usuarios
@app.route("/usuarios")
def listar_usuarios():
    usuarios = []
    for item in senhas_falsas:
        usuarios.append(item["usuario"])
    return jsonify (usuarios)

@app.route("/sites")
def listar_sites():
    sites = []
    for item in senhas_falsas:
        sites.append(item["site"])
    return jsonify(sites)

# Rota 3: Retorna uma senha específica (DESAFIO!)
@app.route("/senha/<int:indice>")
def pegar_senha(indice):
    # Vamos ver se o índice existe
    if indice < 0 or indice >= len(senhas_falsas):
        return jsonify({"erro": "senha não encontrada"}), 404
    return jsonify(senhas_falsas[indice])

# ROTA 4 Retorna senha pelo nome do site
@app.route("/buscar/<nome_site>")
def buscar_por_site(nome_site):
    for item in senhas_falsas:
        if item["site"] == nome_site:
            return jsonify(item)
    return jsonify({"erro": "Site não encontrato"}), 404

@app.route("/adicionar", methods=["POST"])
def adicionar_senha():
    dados = request.get_json()

    if not dados or "site" not in dados or "usuario" not in dados or "senha" not in dados:
        return jsonify({"erro": "Dados incompletos"}), 400
    
    nova_senha = {
        "site": dados["site"],
        "usuario": dados["usuario"],
        "senha": dados["senha"]
    }
                        
    senhas_falsas.append(nova_senha)

    return jsonify({"mensagem": "Senhas adicionada com sucesso!", "senha": nova_senha}), 201

if __name__ == "__main__":
    app.run(debug=True)
