import requests

# Faz uma requisição GET para o servidor
resposta = requests.get("http://127.0.0.1:5000/senhas")

# Verifica se deu certo
if resposta.status_code == 200:
    # Converte o JSON de volta para lista de dicionários
    dados = resposta.json()
    print("Senhas recebidas do sevidor:")
    for senha in dados:
        print (f"Site: {senha['site']}, Usuário: {senha['usuario']}")
else:
    print("Erro ao conectar ao servodr!")