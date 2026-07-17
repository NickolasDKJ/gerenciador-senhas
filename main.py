import json
import secrets 
import string
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

def gerar_chave(senha_mestra, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    chave = base64.urlsafe_b64encode(kdf.derive(senha_mestra.encode()))
    return chave

def obter_salt():
    if os.path.exists("salt.bin"):
        with open("salt.bin", "rb") as arquivo:
            return arquivo.read()
    else:
        salt = os.urandom(16)
        with open("salt.bin", "wb") as arquivo:
            arquivo.write(salt)
        return salt

def criptografar_cofre(senha_mestra):
    salt = obter_salt()
    chave = gerar_chave(senha_mestra, salt)
    f = Fernet(chave)

    dados_texto = json.dumps(cofre).encode()
    dados_criptografados = f.encrypt(dados_texto)

    with open("cofre.dat", "wb") as arquivo:
        arquivo.write(dados_criptografados)

def descriptografar_cofre(senha_mestra):
    if not os.path.exists("cofre.dat"):
        return[]
    
    salt = obter_salt()
    chave = gerar_chave(senha_mestra, salt)
    f = Fernet(chave)

    with open("cofre.dat", "rb") as arquivo:
        dados_criptografados = arquivo.read()

    dados_texto = f.decrypt(dados_criptografados)
    return json.loads(dados_texto)


def ja_existe(site, usuario):
    for item in cofre:
        if item["site"].lower() == site.lower() and item["usuario"].lower() == usuario.lower():
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

while True:
    senha_mestra = input("Digite sua senha mestra:")
    try:
        cofre = descriptografar_cofre(senha_mestra)
        break
    except InvalidToken:
        print("Senha mestra incorreta. Tente novamente.")

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

        if ja_existe(site, usuario):
            print("Já existe uma senha cadastrada para esse usuário nesse site!")
        else:
            escolha_senha = input("Digite (1) para gerar senha automática ou (2) para digitar a sua: ")
            if escolha_senha == "1":
                senha = gerar_senha()
                print("Senha gerada")
            else:
                senha = input("Senha: ")

            adicionar_senha(site, usuario, senha)
            criptografar_cofre(senha_mestra)
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
