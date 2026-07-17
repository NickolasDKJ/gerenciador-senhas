import json
import secrets 
import string



def salvar_cofre():
    with open("cofre.json", "w") as arquivo:
        json.dump(cofre, arquivo, indent=4)

def carregar_cofre():
    try:
        with open("cofre.json", "r") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return []

def ja_existe(site, usuario):
    for item in cofre:
        if item["site"] == site and item["usuario"] == usuario:
            return True
    return False

def gerar_senha(tamanho=16):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha = "".join(secrets.choice(caracteres) for _ in range(tamanho))
    return senha

def adicionar_senha(site, usuario, senha):
    nova_entrada = {"site": site, "usuario": usuario, "senha": senha}
    cofre.append(nova_entrada)
    print("Senha adicionada com sucesso!")

cofre = carregar_cofre()

rodando = True

while rodando:
    print("=== Gerenciador de Senhas ===")
    print("1 - Adicionar senha")
    print("2 - Listar senhas")
    print("3 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        site = input("Site: ")
        usuario = input("Usuário: ")
        escolha_senha = input("Digite (1) para gerar senha automática ou (2) para digita a sua: ")
        if escolha_senha == "1":
            senha = gerar_senha()
            print("Senha gerada")
        else:
            senha = input("Senha: ")
        if ja_existe(site,usuario):
            print("Já existe uma senha cadastrada para esse usuário nesse site!")
        else:
            adicionar_senha(senha, usuario, senha)
            salvar_cofre()
    elif opcao == "2":
        if len(cofre) == 0:
            print("Nenhuma senha cadastrada ainda.")
        else:
            for item in cofre:
                print(item["site"], "-", item["usuario"], "-", item["senha"])
    elif opcao == "3":
        print("Saindo...")
        rodando = False
    else:
        print("Opção inválida")
