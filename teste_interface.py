import tkinter as tk
import json
import secrets 
import string
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import time

tentativas = 0

def tentar_entrar():
    global tentativas, cofre

    segundos_restantes = verificar_bloqueio()
    if segundos_restantes > 0:
        atualizar_contador()
        return

    senha_digitada = campo_senha.get()
    try:
        cofre = descriptografar_cofre(senha_digitada)
        janela.destroy()
        abrir_tela_principal(senha_digitada)
    except InvalidToken:
        tentativas = tentativas + 1
        restantes = 3 - tentativas
        if restantes <= 0:
            bloquear(60)
            atualizar_contador()
        else:
            mensagem.config(text="Senha incorreta. Tentativas restantes: " + str(restantes))


def abrir_tela_principal (senha_mestra):
    tela_principal = tk.Tk()
    tela_principal.title("Gerenciador de Senhas")
    tela_principal.geometry("400x300")

    titulo = tk.Label(tela_principal, text="Bem-vindo ao seu cofre!")
    titulo.pack(pady=10)

    botao_adicionar = tk.Button(tela_principal, text="Adicionar Senha", command=lambda: janela_adicionar(tela_principal))
    botao_adicionar.pack(pady=5)

    botao_listar = tk.Button(tela_principal, text="Listar Senhas")
    botao_listar.pack(pady=5)
    
    tela_principal.mainloop()

def janela_adicionar(pai):
    popup = tk.Toplevel(pai)
    popup.title("Adicionar Senha")
    popup.geometry("300x250")

    tk.Label(popup, text="Site:").pack()
    campo_site = tk.Entry(popup)
    campo_site.pack()

    tk.Label(popup, text="Usuário:").pack()
    campo_usuario = tk.Entry(popup)
    campo_usuario.pack()

    tk.Label(popup, text="Senha:").pack()
    campo_senha_nova = tk.Entry(popup)
    campo_senha_nova.pack()

    aviso = tk.Label(popup, text="")
    aviso.pack()
    def gerar():
        senha_gerada = gerar_senha()
        campo_senha_nova.delete(0, tk.END)
        campo_senha_nova.insert(0, senha_gerada)
    
    botao_gerar = tk.Button(popup, text="Gerar senha", command=gerar)
    botao_gerar.pack(pady=5)
    
def bloquear(segundos_bloqueio):
    horario_liberacao = time.time() + segundos_bloqueio
    with open("bloqueio.txt", "w") as arquivo:
        arquivo.write(str(horario_liberacao))

def atualizar_contador():
    segundos = verificar_bloqueio()
    if segundos >0:
        mensagem.config(text="Bloqueio. Tente em " + str(int(segundos)) + "s.")
        janela.after(1000, atualizar_contador)  # chama de novo em 1 segundo
    else:
        mensagem.config(text="Pode tentar novamente.")

def verificar_bloqueio():
    if not os.path.exists("bloqueio.txt"):
        return 0
    with open("bloqueio.txt", "r") as arquivo:
        horario_liberacao = float(arquivo.read())

    segundos_restantes = horario_liberacao - time.time()

    if segundos_restantes > 0:
        return segundos_restantes
    else:
        os.remove("bloqueio.txt")
        return 0
    
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


janela = tk.Tk()
janela.title("Login - Gerenciador de Senhas")
janela.geometry("300x150")

label_senha = tk.Label(janela, text="Senhas mestra:")
label_senha.pack()

campo_senha = tk.Entry(janela, show="*")
campo_senha.pack()

botao_entrar = tk.Button(janela, text="Entrar", command=tentar_entrar)
botao_entrar.pack()

mensagem = tk.Label(janela, text="")
mensagem.pack()

janela.mainloop()
