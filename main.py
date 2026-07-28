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
import requests 

# ============================================
# CONFIGURAÇÕES GLOBAIS
# ============================================

URL_SERVIDOR = "http://127.0.0.1:5000"
tentativas = 0
cofre = []

# ============================================
# FUNÇÕES DE BLOQUEIO E SEGURANÇA
# ============================================

def bloquear(segundos_bloqueio):
    horario_liberacao = time.time() + segundos_bloqueio
    with open("bloqueio.txt", "w") as arquivo:
        arquivo.write(str(horario_liberacao))

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

def atualizar_contador():
    segundos = verificar_bloqueio()
    if segundos > 0:
        mensagem.config(text="Bloqueio. Tente em " + str(int(segundos)) + "s.")
        janela.after(1000, atualizar_contador)
    else:
        mensagem.config(text="Pode tentar novamente.")

# ============================================
# FUNÇÕES DE CRIPTOGRAFIA
# ============================================

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
        return []
    salt = obter_salt()
    chave = gerar_chave(senha_mestra, salt)
    f = Fernet(chave)
    with open("cofre.dat", "rb") as arquivo:
        dados_criptografados = arquivo.read()
    dados_texto = f.decrypt(dados_criptografados)
    return json.loads(dados_texto)

# ============================================
# FUNÇÕES DE COMUNICAÇÃO COM SERVIDOR
# ============================================

def buscar_senhas_do_servidor():
    """Tenta buscar as senhas do servidor. Se falhar, retorna None."""
    try:
        resposta = requests.get(f"{URL_SERVIDOR}/senhas", timeout=2)
        if resposta.status_code == 200:
            return resposta.json()
        else:
            print(f"Servidor respondeu com erro: {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("Servidor não está rodando. Usando arquivo local...")
        return None
    except requests.exceptions.Timeout:
        print("Servidor demorou para responder. Usando arquivo local...")
        return None

def enviar_para_servidor(site, usuario, senha):
    """Tenta enviar a nova senha para o servidor. Retorna True se deu certo."""
    try:
        dados = {
            "site": site,
            "usuario": usuario,
            "senha": senha
        }
        resposta = requests.post(f"{URL_SERVIDOR}/adicionar", json=dados, timeout=2)
        if resposta.status_code == 201:
            print("✅ Senha enviada ao servidor com sucesso!")
            return True
        else:
            print(f"❌ Servidor respondeu com erro: {resposta.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Servidor offline. Senha salva apenas localmente.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Servidor demorou para responder. Salva apenas local.")
        return False

def salvar_pendente(site, usuario, senha):
    """Salva uma senha para ser sincronizada depois"""
    pendentes = []
    if os.path.exists("pendentes.json"):
        with open("pendentes.json", "r") as f:
            pendentes = json.load(f)
    pendentes.append({
        "site": site,
        "usuario": usuario,
        "senha": senha
    })
    with open("pendentes.json", "w") as f:
        json.dump(pendentes, f)

def sincronizar_pendentes():
    """Tenta enviar todas as senhas pendentes para o servidor"""
    if not os.path.exists("pendentes.json"):
        return
    with open("pendentes.json", "r") as f:
        pendentes = json.load(f)
    if not pendentes:
        return
    print(f"🔄 Tentando sincronizar {len(pendentes)} senhas pendentes...")
    sincronizadas = []
    falhas = []
    for item in pendentes:
        sucesso = enviar_para_servidor(
            item["site"],
            item["usuario"],
            item["senha"]
        )
        if sucesso:
            sincronizadas.append(item)
        else:
            falhas.append(item)
    with open("pendentes.json", "w") as f:
        json.dump(falhas, f)
    print(f"✅ {len(sincronizadas)} sincronizadas, {len(falhas)} pendentes")
    return len(sincronizadas), len(falhas)

# ============================================
# FUNÇÕES DE GERENCIAMENTO DO COFRE
# ============================================

def adicionar_senha(site, usuario, senha):
    nova_entrada = {"site": site, "usuario": usuario, "senha": senha}
    cofre.append(nova_entrada)
    print("Senha adicionada com sucesso!")

def ja_existe(site, usuario):
    for item in cofre:
        if item["site"].lower() == site.lower() and item["usuario"].lower() == usuario.lower():
            return True
    return False

def gerar_senha(tamanho=16):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha = "".join(secrets.choice(caracteres) for _ in range(tamanho))
    return senha

# ============================================
# FUNÇÕES AUXILIARES DA INTERFACE
# ============================================

def gerar_senha_no_campo(campo):
    """Gera uma senha e coloca no campo"""
    senha_gerada = gerar_senha()
    campo.delete(0, tk.END)
    campo.insert(0, senha_gerada)

def salvar_senha(campo_site, campo_usuario, campo_senha_nova, aviso, senha_mestra, popup):
    """Salva a senha (local + servidor)"""
    site = campo_site.get()
    usuario = campo_usuario.get()
    senha = campo_senha_nova.get()
    
    if not site or not usuario or not senha:
        aviso.config(text="⚠️ Preencha todos os campos!", fg="red")
        return
    
    if ja_existe(site, usuario):
        aviso.config(text="⚠️ Já existe cadastro para esse site/usuário!", fg="red")
        return
    
    # Adiciona localmente
    adicionar_senha(site, usuario, senha)
    
    # Tenta enviar para o servidor
    sucesso = enviar_para_servidor(site, usuario, senha)
    
    # Salva localmente (sempre)
    criptografar_cofre(senha_mestra)
    
    if sucesso:
        aviso.config(text="✅ Senha salva no servidor e localmente!", fg="green")
    else:
        salvar_pendente(site, usuario, senha)
        aviso.config(text="⚠️ Servidor offline! Salva localmente (pendente)", fg="orange")
    
    # Limpa os campos
    campo_site.delete(0, tk.END)
    campo_usuario.delete(0, tk.END)
    campo_senha_nova.delete(0, tk.END)

# ============================================
# TELAS DA INTERFACE
# ============================================

def tentar_entrar():
    global tentativas, cofre

    segundos_restantes = verificar_bloqueio()
    if segundos_restantes > 0:
        atualizar_contador()
        return

    senha_digitada = campo_senha.get()
    try:
        sincronizar_pendentes()
        senhas = buscar_senhas_do_servidor()
        if senhas is None:
            senhas = descriptografar_cofre(senha_digitada)
            print("📁 Modo offline - usando arquivo local")
        else:
            print("🌐 Modo online - dados do servidor")
        
        cofre = senhas
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

def abrir_tela_principal(senha_mestra):
    tela_principal = tk.Tk()
    tela_principal.title("Gerenciador de Senhas")
    tela_principal.geometry("400x300")

    titulo = tk.Label(tela_principal, text="Bem-vindo ao seu cofre!")
    titulo.pack(pady=10)

    botao_adicionar = tk.Button(
        tela_principal, 
        text="Adicionar Senha", 
        command=lambda: janela_adicionar(tela_principal, senha_mestra)
    )
    botao_adicionar.pack(pady=5)

    botao_listar = tk.Button(
        tela_principal, 
        text="Listar Senhas", 
        command=lambda: janela_listar(tela_principal)
    )
    botao_listar.pack(pady=5)
    
    tela_principal.mainloop()

def janela_adicionar(pai, senha_mestra):
    popup = tk.Toplevel(pai)
    popup.title("Adicionar Senha")
    popup.geometry("400x400")
    popup.resizable(False, False)

    tk.Label(popup, text="🔐 Nova Senha", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Frame(popup, height=2, bg="gray").pack(fill="x", padx=20, pady=5)

    frame_campos = tk.Frame(popup)
    frame_campos.pack(pady=10, padx=20, fill="x")

    tk.Label(frame_campos, text="Site:", font=("Arial", 10, "bold"), anchor="w").pack(fill="x")
    campo_site = tk.Entry(frame_campos, width=40)
    campo_site.pack(pady=(0,10), fill="x")

    tk.Label(frame_campos, text="Usuário:", font=("Arial", 10, "bold"), anchor="w").pack(fill="x")
    campo_usuario = tk.Entry(frame_campos, width=40)
    campo_usuario.pack(pady=(0,10), fill="x")

    tk.Label(frame_campos, text="Senha:", font=("Arial", 10, "bold"), anchor="w").pack(fill="x")
    campo_senha_nova = tk.Entry(frame_campos, width=40)
    campo_senha_nova.pack(pady=(0,5), fill="x")

    aviso = tk.Label(popup, text="", fg="blue", font=("Arial", 9))
    aviso.pack(pady=5)

    tk.Frame(popup, height=2, bg="gray").pack(fill="x", padx=20, pady=5)

    frame_botoes = tk.Frame(popup)
    frame_botoes.pack(pady=10)

    botao_gerar = tk.Button(
        frame_botoes, 
        text="🔑 Gerar Senha", 
        command=lambda: gerar_senha_no_campo(campo_senha_nova),
        bg="#e0e0e0",
        width=20,
        height=1
    )
    botao_gerar.pack(pady=5)

    botao_salvar = tk.Button(
        frame_botoes, 
        text="💾 Salvar Senha", 
        command=lambda: salvar_senha(
            campo_site, 
            campo_usuario, 
            campo_senha_nova, 
            aviso, 
            senha_mestra,
            popup
        ),
        bg="#4CAF50",
        fg="white",
        width=20,
        height=1
    )
    botao_salvar.pack(pady=5)

    botao_fechar = tk.Button(
        frame_botoes,
        text="❌ Cancelar",
        command=popup.destroy,
        bg="#f44336",
        fg="white",
        width=20,
        height=1
    )
    botao_fechar.pack(pady=5)

def janela_listar(pai):
    popup = tk.Toplevel(pai)
    popup.title("Suas senhas")
    popup.geometry("400x300")

    if len(cofre) == 0:
        tk.Label(popup, text="Nenhuma senha cadastrada ainda.").pack()
    else:
        for item in cofre:
            linha = tk.Frame(popup)
            linha.pack(fill="x", pady=2)

            texto = item["site"] + " - " + item["usuario"] + " - " + item["senha"]
            tk.Label(linha, text=texto, anchor="w").pack(side="left", fill="x", expand=True)

            def copiar(senha=item["senha"]):
                popup.clipboard_clear()
                popup.clipboard_append(senha)
            tk.Button(linha, text="Copiar", command=copiar).pack(side="right")

# ============================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ============================================

janela = tk.Tk()
janela.title("Login - Gerenciador de Senhas")
janela.geometry("300x150")

label_senha = tk.Label(janela, text="Senha mestra:")
label_senha.pack()

campo_senha = tk.Entry(janela, show="*")
campo_senha.pack()

botao_entrar = tk.Button(janela, text="Entrar", command=tentar_entrar)
botao_entrar.pack()

mensagem = tk.Label(janela, text="")
mensagem.pack()

janela.mainloop()