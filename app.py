# ==================================================
# © 2026 JOBOSAN — SISTEMA COMPLETO FUNCIONAL ✅
# REDE SOCIAL · CADASTRO PERMANENTE · MÍDIA · JOGOS · IA · DNA
# PORTA 5000 ✅
# ==================================================

from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, render_template_string
import hashlib
import base64
import os
import random
import sqlite3
import uuid
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

# --------------------------------------------------
# ⚙️ CONFIGURAÇÕES
# --------------------------------------------------
NOME_APLICACAO = "Jobosan"
CHAVE_SESSAO_PADRAO = "JOBOSAN_REDE_SOCIAL_2026_SEGURA"

app = Flask(__name__)
app.secret_key = os.environ.get("CHAVE_UNIFICADA", CHAVE_SESSAO_PADRAO)
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=3650)  # 10 anos

# Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "ahwrdxaw"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "945329764752813"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "EQQEG"),
    secure=True
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANCO_DADOS = os.path.join(os.path.dirname(BASE_DIR), "jobosan_novo.db")


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "webm"}

EMAIL_DONO = "joasilva19577@gmail.com"
SENHA_MESTRA_ACESSO = "JOBOSAn@2026#DONO"

# --------------------------------------------------
# 🗄️ BANCO DE DADOS
# --------------------------------------------------
def get_db():
    conn = sqlite3.connect(BANCO_DADOS)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        pontos INTEGER DEFAULT 0,
        dna_chave TEXT NOT NULL,
        data_cadastro TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS postagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        texto TEXT,
        arquivo TEXT,
        data_postagem TEXT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS curtidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        postagem_id INTEGER NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (postagem_id) REFERENCES postagens(id),
        UNIQUE(usuario_id, postagem_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS conversas_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        pergunta TEXT NOT NULL,
        resposta TEXT NOT NULL,
        data_hora TEXT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS regras_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta_chave TEXT UNIQUE NOT NULL,
        resposta_customizada TEXT NOT NULL
    )""")
    conn.commit()
    conn.close()

init_db()

# --------------------------------------------------
# 🔒 FUNÇÕES DE VERIFICAÇÃO
# --------------------------------------------------
def usuario_logado():
    return "usuario_id" in session

def eh_dono():
    if not usuario_logado():
        return False
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT email FROM usuarios WHERE id = ?", (session["usuario_id"],))
        usuario = c.fetchone()
        conn.close()
        return usuario and usuario["email"].strip().lower() == EMAIL_DONO.lower()
    except:
        return False

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------------------------------
# 🤖 MOTOR DA IA
# --------------------------------------------------
def responder_ia(pergunta):
    p = pergunta.lower().strip()
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT resposta_customizada FROM regras_ia WHERE ? LIKE '%' || pergunta_chave || '%'", (p,))
        regra = c.fetchone()
        conn.close()
        if regra:
            return regra["resposta_customizada"]
    except:
        pass

    if "brasil" in p and ("descobriu" in p or "ano" in p):
        return "O Brasil foi descoberto em 22 de abril de 1500 por Pedro Álvares Cabral."
    elif "quem é você" in p or "quem criou" in p:
        return f"Eu sou a IA da {NOME_APLICACAO}, criada por João Bento da Silva."
    elif "jogo" in p and "cartas" in p:
        return "🃏 Y→Y, A→Z, Z→A, B→X, X→B, C→G, G→C, D→F, F→D, E→E."
    elif "bentinho" in p or "números" in p:
        return "🎮 0→0, 1→9, 2→8, 3→7, 4→6, 5→5, 6→4, 7→3, 8→2, 9→1."
    elif "dna" in p:
        return "🧬 Cada usuário tem sua chave única. Salve o .bnj no celular!"
    elif "oi" in p or "olá" in p:
        return f"Olá! 👋 Bem-vindo ao {NOME_APLICACAO}!"
    else:
        return f"Entendi! Você perguntou: \"{pergunta}\""

# --------------------------------------------------
# 🏠 TELA INICIAL
# --------------------------------------------------
@app.route("/")
def inicio():
    if usuario_logado():
        return redirect(url_for("plataforma"))
    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{NOME_APLICACAO}</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;}}
        body{{background:linear-gradient(180deg,#0f172a,#1e293b);color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;}}
        .caixa{{background:rgba(15,23,42,0.8);padding:40px;border-radius:12px;border:1px solid #f59e0b;width:90%;max-width:400px;}}
        h1{{color:#f59e0b;text-align:center;margin-bottom:30px;}}
        input{{width:100%;padding:12px;margin:8px 0;background:#020617;border:1px solid #334155;color:white;border-radius:6px;}}
        button{{width:100%;padding:12px;background:#f59e0b;color:#1e1b16;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}}
        .link{{text-align:center;margin-top:15px;font-size:14px;color:#94a3b8;}}
        .link a{{color:#f59e0b;text-decoration:none;}}
    </style>
</head>
<body>
    <div class="caixa">
        <h1>{NOME_APLICACAO}</h1>
        <form action="/entrar" method="POST">
            <input type="email" name="email" placeholder="E-mail" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit">Entrar</button>
        </form>
        <div class="link">Não tem conta? <a href="/cadastrar">Cadastre-se — PERMANENTE ✅</a></div>
    </div>
</body>
</html>''')

# --------------------------------------------------
# ✅ CADASTRO PERMANENTE — CORRIGIDO
# --------------------------------------------------
@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if usuario_logado():
        return redirect(url_for("plataforma"))
    
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()
        
        if nome and email and senha:
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            dna_chave = base64.b64encode(os.urandom(24)).decode()
            data_cad = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = None
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
                if c.fetchone():
                    return '''<div style="text-align:center;padding:50px;background:#0f172a;color:white;">
                        <h2 style="color:red;">E-mail já cadastrado! Faça login.</h2>
                        <br><a href="/" style="color:#f59e0b;font-size:18px;">Ir para Login</a>
                    </div>'''

                c.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash, dna_chave, data_cadastro) VALUES (?, ?, ?, ?, ?)",
                    (nome, email, senha_hash, dna_chave, data_cad)
                )
                conn.commit()
                usuario_id = c.lastrowid
                
                session.permanent = True
                session["usuario_id"] = usuario_id
                session["nome_usuario"] = nome
                
                return redirect(url_for("plataforma"))
            except Exception as e:
                return f'''<div style="text-align:center;padding:50px;background:#0f172a;color:white;">
                    <h2 style="color:red;">Erro ao cadastrar: {str(e)}</h2>
                    <br><a href="/cadastrar" style="color:#f59e0b;font-size:18px;">Tentar novamente</a>
                </div>'''
            finally:
                if conn:
                    conn.close()

    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cadastrar — {NOME_APLICACAO}</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;}}
        body{{background:linear-gradient(180deg,#0f172a,#1e293b);color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;}}
        .caixa{{background:rgba(15,23,42,0.8);padding:40px;border-radius:12px;border:1px solid #f59e0b;width:90%;max-width:400px;}}
        h1{{color:#f59e0b;text-align:center;margin-bottom:30px;}}
        input{{width:100%;padding:12px;margin:8px 0;background:#020617;border:1px solid #334155;color:white;border-radius:6px;}}
        button{{width:100%;padding:12px;background:#f59e0b;color:#1e1b16;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}}
        .link{{text-align:center;margin-top:15px;font-size:14px;color:#94a3b8;}}
        .link a{{color:#f59e0b;text-decoration:none;}}
    </style>
</head>
<body>
    <div class="caixa">
        <h1>Cadastrar ✅ PERMANENTE</h1>
        <form method="POST">
            <input type="text" name="nome" placeholder="Seu nome" required>
            <input type="email" name="email" placeholder="E-mail" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit">Cadastrar — Para Sempre</button>
        </form>
        <div class="link">Já tem conta? <a href="/">Entrar</a></div>
    </div>
</body>
</html>''')

# --------------------------------------------------
# 🔑 ENTRAR
# --------------------------------------------------
@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if usuario_logado():
        return redirect(url_for("plataforma"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()
        
        if email and senha:
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            conn = None
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT id, nome FROM usuarios WHERE email = ? AND senha_hash = ?", (email, senha_hash))
                usuario = c.fetchone()
                
                if usuario:
                    session.permanent = True
                    session["usuario_id"] = usuario[0] if isinstance(usuario, tuple) else usuario["id"]
                    session["nome_usuario"] = usuario[1] if isinstance(usuario, tuple) else usuario["nome"]
                    return redirect(url_for("plataforma"))
                else:
                    return '''<div style="text-align:center;padding:50px;background:#0f172a;color:white;">
                        <h2 style="color:red;">E-mail ou senha inválidos!</h2>
                        <br><a href="/entrar" style="color:#f59e0b;font-size:18px;">Tentar novamente</a>
                    </div>'''
            except Exception as e:
                return f'''<div style="text-align:center;padding:50px;background:#0f172a;color:white;">
                    <h2 style="color:red;">Erro ao entrar: {str(e)}</h2>
                    <br><a href="/entrar" style="color:#f59e0b;font-size:18px;">Voltar</a>
                </div>'''
            finally:
                if conn:
                    conn.close()

    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Entrar — {NOME_APLICACAO}</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;}}
        body{{background:linear-gradient(180deg,#0f172a,#1e293b);color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;}}
        .caixa{{background:rgba(15,23,42,0.8);padding:40px;border-radius:12px;border:1px solid #f59e0b;width:90%;max-width:400px;}}
        h1{{color:#f59e0b;text-align:center;margin-bottom:30px;}}
        input{{width:100%;padding:12px;margin:8px 0;background:#020617;border:1px solid #334155;color:white;border-radius:6px;}}
        button{{width:100%;padding:12px;background:#f59e0b;color:#1e1b16;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}}
        .link{{text-align:center;margin-top:15px;font-size:14px;color:#94a3b8;}}
        .link a{{color:#f59e0b;text-decoration:none;}}
    </style>
</head>
<body>
    <div class="caixa">
        <h1>Entrar 🔑</h1>
        <form method="POST">
            <input type="email" name="email" placeholder="Seu E-mail" required>
            <input type="password" name="senha" placeholder="Sua Senha" required>
            <button type="submit">Entrar na Conta</button>
        </form>
        <div class="link">Não tem conta? <a href="/cadastrar">Cadastre-se</a></div>
    </div>
</body>
</html>''')

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("inicio"))

# --------------------------------------------------
# 🔒 ÁREA PRIVADA
# --------------------------------------------------
@app.route("/area_privada", methods=["GET", "POST"])
def area_privada():
    if not usuario_logado() or not eh_dono():
        return '''<div style="text-align:center;padding:50px;background:#0f172a;color:white;">
            <h2 style="color:red;">🚫 ACESSO NEGADO — Área exclusiva do dono</h2>
            <br><a href="/plataforma" style="color:#f59e0b;">Voltar</a>
        </div>'''
    if request.method == "POST":
        if request.form.get("senha_mestra") == SENHA_MESTRA_ACESSO:
            return redirect(url_for("painel_dono"))
        return '''<div style="text-align:center;padding:50px;background:#0f172a;color:white;">
            <h2 style="color:red;">❌ Senha incorreta!</h2>
            <br><a href="/area_privada" style="color:#f59e0b;">Tentar novamente</a>
        </div>'''
    return render_template_string('''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 Área Privada</title>
    <style>body{background:linear-gradient(180deg,#0f172a,#1e293b);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:Arial,sans-serif;}
    .caixa{background:rgba(15,23,42,0.9);padding:40px;border-radius:12px;border:2px solid #f59e0b;max-width:400px;width:90%;text-align:center;}
    h1{color:#f59e0b;margin-bottom:20px;}
    input{width:100%;padding:12px;margin:8px 0;background:#020617;border:1px solid #334155;color:white;border-radius:6px;}
    button{width:100%;padding:12px;background:#f59e0b;color:black;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}
    a{color:#f59e0b;text-decoration:none;display:block;margin-top:20px;}</style>
</head>
<body>
    <div class="caixa">
        <h1>🔒 ÁREA PRIVADA</h1>
        <p style="margin-bottom:20px;">Confirme a senha mestra para acessar</p>
        <form method="POST">
            <input type="password" name="senha_mestra" placeholder="Senha Mestra" required>
            <button type="submit">🔓 Desbloquear</button>
        </form>
        <a href="/plataforma">← Voltar</a>
    </div>
</body>
</html>''')

@app.route("/painel_dono")
def painel_dono():
    if not usuario_logado() or not eh_dono():
        return redirect(url_for("inicio"))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM postagens")
    total_postagens = c.fetchone()[0]
    conn.close()
    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚙️ Painel do Dono</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body{{background:linear-gradient(180deg,#0f172a,#1e293b);color:#e2e8f0;min-height:100vh;}}</style>
</head>
<body class="p-6 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-yellow-500 mb-6">⚙️ PAINEL DO DONO</h1>
    <a href="/plataforma" class="text-yellow-500 mb-4 inline-block">← Voltar</a>
    <div class="grid grid-cols-2 gap-4">
        <div class="bg-gray-800 p-4 rounded-lg border border-yellow-500/30">
            <p class="text-gray-400">Total de Usuários</p>
            <p class="text-2xl font-bold text-yellow-500">{total_usuarios}</p>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg border border-yellow-500/30">
            <p class="text-gray-400">Total de Postagens</p>
            <p class="text-2xl font-bold text-yellow-500">{total_postagens}</p>
        </div>
    </div>
</body>
</html>''')

# --------------------------------------------------
# 🤖 ROTAS DA IA
# --------------------------------------------------
@app.route("/responder_ia", methods=["POST"])
def responder_ia_rota():
    if not usuario_logado():
        return "Não autorizado", 401
    pergunta = request.form.get("pergunta", "").strip()
    if not pergunta:
        return "Digite uma pergunta!"
    resposta = responder_ia(pergunta)
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO conversas_ia (usuario_id, pergunta, resposta, data_hora) VALUES (?, ?, ?, ?)",
              (session["usuario_id"], pergunta, resposta, data_hora))
    conn.commit()
    conn.close()
    return resposta

@app.route("/ensinar_ia", methods=["POST"])
def ensinar_ia():
    if not usuario_logado():
        return "Não autorizado", 401
    pergunta_chave = request.form.get("pergunta_chave", "").strip().lower()
    resposta_customizada = request.form.get("resposta_customizada", "").strip()
    if pergunta_chave and resposta_customizada:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO regras_ia (pergunta_chave, resposta_customizada) VALUES (?, ?)", 
                      (pergunta_chave, resposta_customizada))
            conn.commit()
            conn.close()
            return "✅ IA ensinada com sucesso!"
        except Exception as e:
            return f"❌ Erro ao ensinar IA: {str(e)}"
    return "Preencha todos os campos!", 400

# --------------------------------------------------
# 🎮 JOGO DAS CARTAS
# --------------------------------------------------
@app.route("/jogo_cartas", methods=["GET", "POST"])
def jogo_cartas():
    if not usuario_logado():
        return redirect(url_for("inicio"))
    REGRAS = {'Y':'Y','A':'Z','Z':'A','B':'X','X':'B','C':'G','G':'C','D':'F','F':'D','E':'E'}
    CARTAS = ['Y','A','B','C','D','E','F','G','X','Z']
    if "cartas_fase" not in session: session["cartas_fase"] = 1
    if "cartas_pontos" not in session: session["cartas_pontos"] = 0
    fase = session["cartas_fase"]
    pontos = session["cartas_pontos"]
    qtd = {1:3,2:6,3:8,4:9}[fase]
    valor = {1:100,2:300,3:500,4:1000}[fase]
    if "cartas_alvo" not in session or len(session.get("cartas_alvo",[])) != qtd:
        session["cartas_alvo"] = random.sample(CARTAS, qtd)
        session["cartas_resposta"] = []
    alvo = session["cartas_alvo"]
    resposta = session["cartas_resposta"]
    msg = ""
    if request.method == "POST":
        if "nova" in request.form:
            session["cartas_alvo"] = random.sample(CARTAS, qtd)
            session["cartas_resposta"] = []
        elif "selecionar" in request.form:
            resposta.append(request.form["selecionar"])
            session["cartas_resposta"] = resposta
        elif "verificar" in request.form:
            if len(resposta) != len(alvo):
                msg = "❌ Selecione todas!"
            else:
                correta = [REGRAS[c] for c in alvo]
                if resposta == correta:
                    pontos += valor
                    session["cartas_pontos"] = pontos
                    msg = f"✅ ACERTOU! +{valor} PONTOS!"
                    try:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (valor, session["usuario_id"]))
                        conn.commit()
                        conn.close()
                    except: pass
                    if fase < 4:
                        session["cartas_fase"] += 1
                        session.pop("cartas_alvo", None)
                    else:
                        msg = "🏆 VENCEU!"
                        session["cartas_fase"] = 1
                        session.pop("cartas_alvo", None)
                else:
                    msg = "❌ Errou!"
                    session["cartas_resposta"] = []
    alvo_html = "".join([f"<span style='background:#f59e0b;color:black;padding:12px 18px;border-radius:8px;margin:5px;font-size:24px;font-weight:bold;'>{c}</span>" for c in alvo])
    resp_html = "".join([f"<span style='background:#22c55e;color:black;padding:12px 18px;border-radius:8px;margin:5px;font-size:24px;font-weight:bold;'>{c}</span>" for c in resposta]) if resposta else "<p style='color:#94a3b8;'>Clique nas cartas...</p>"
    disp_html = "".join([f"<button type='submit' name='selecionar' value='{c}' style='background:#33415e;color:white;padding:12px 18px;border-radius:8px;margin:5px;font-size:24px;font-weight:bold;border:2px solid #f59e0b;cursor:pointer;'>{c}</button>" for c in CARTAS])
    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🃏 Jogo das Cartas</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body{{background:linear-gradient(180deg,#0f172a,#1e293b);color:#e2e8f0;min-height:100vh;}}</style>
</head>
<body class="p-6 max-w-2xl mx-auto">
    <a href="/plataforma" class="text-yellow-500">← Voltar</a>
    <h1 class="text-4xl font-bold text-yellow-500 text-center my-6">🃏 Jogo das Cartas</h1>
    <p class="text-center text-lg mb-4">Fase {fase}/4 · Pontos: {pontos}</p>
    {f'<div class="text-center p-3 rounded-lg mb-4 text-lg font-bold {"bg-green-900/50 text-green-400" if "✅" in msg or "🏆" in msg else "bg-red-900/50 text-red-400"}">{msg}</div>' if msg else ''}
    <div class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 mb-5">
        <p class="text-center mb-3 text-gray-400">🎯 Cartas Alvo:</p>
        <div class="flex flex-wrap justify-center">{alvo_html}</div>
    </div>
    <div class="bg-gray-800 p-5 rounded-lg border border-green-500/30 mb-5">
        <p class="text-center mb-3 text-gray-400">✅ Sua Resposta:</p>
        <div class="flex flex-wrap justify-center">{resp_html}</div>
    </div>
    <form method="POST" class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 mb-5">
        <p class="text-center mb-3 text-gray-400">🃏 Clique para selecionar:</p>
        <div class="flex flex-wrap justify-center">{disp_html}</div>
    </form>
    <div class="flex gap-3 justify-center">
        <form method="POST"><button type="submit" name="verificar" class="bg-green-600 text-white font-bold px-6 py-3 rounded-lg">✅ Verificar</button></form>
        <form method="POST"><button type="submit" name="nova" class="bg-yellow-600 text-black font-bold px-6 py-3 rounded-lg">🔄 Novas</button></form>
    </div>
</body>
</html>''')

# --------------------------------------------------
# 🎮 JOGO BENTINHO
# --------------------------------------------------
@app.route("/jogo_bentinho", methods=["GET", "POST"])
def jogo_bentinho():
    if not usuario_logado():
        return redirect(url_for("inicio"))
    
    TABELA = {'0':'0', '1':'9', '2':'8', '3':'7', '4':'6', '5':'5', '6':'4', '7':'3', '8':'2', '9':'1'}
    def inverter(num): 
        return "".join(TABELA.get(str(d), d) for d in str(num))
    
    if "bent_fase" not in session: session["bent_fase"] = 1
    if "bent_pontos" not in session: session["bent_pontos"] = 0
        
    fase_atual = int(session.get("bent_fase", 1))
    tamanhos = {1: 3, 2: 6, 3: 8, 4: 9}
    tam = tamanhos.get(fase_atual, 3)
    
    if "bent_num" not in session or session.get("bent_fase_atual") != fase_atual:
        session["bent_num"] = "".join(random.choice("0123456789") for _ in range(tam))
        session["bent_alvo"] = inverter(session["bent_num"])
        session["bent_fase_atual"] = fase_atual

    msg = ""
    PTS = {1: 250000, 2: 2500000, 3: 25000000, 4: 1000000000}
    
    if request.method == "POST":
        acao = request.form.get("acao", "")
        if acao == "reiniciar":
            session["bent_fase"] = 1
            session["bent_pontos"] = 0
            session.pop("bent_num", None)
            session.pop("bent_fase_atual", None)
            return redirect(url_for("jogo_bentinho"))
            
        resp = request.form.get("resposta", "").strip()
        alvo_salvo = session.get("bent_alvo", "")
        
        if resp and resp == alvo_salvo:
            pts = PTS.get(fase_atual, 250000)
            session["bent_pontos"] += pts
            msg = f"✅ ACERTOU! +{pts:,} PONTOS!"
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (pts, session["usuario_id"]))
                conn.commit()
                conn.close()
            except: pass
                
            if fase_atual < 4:
                session["bent_fase"] = fase_atual + 1
                session.pop("bent_num", None)
                session.pop("bent_fase_atual", None)
            else:
                msg = "🏆 PARABÉNS! 1.000.000.000 DE PONTOS!"
                session["bent_fase"] = 1
                session["bent_pontos"] = 0
                session.pop("bent_num", None)
                session.pop("bent_fase_atual", None)
        else:
            msg = "❌ Errou! Tente novamente."

    num_exibicao = session.get("bent_num", "000")
    pontos_atuais = session.get("bent_pontos", 0)

    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 Segredo dos Números</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body{{background:linear-gradient(180deg,#0f172a,#1e293b);color:#e2e8f0;min-height:100vh;}}</style>
</head>
<body class="flex items-center justify-center p-4">
    <div class="bg-gray-800 p-8 rounded-xl border-2 border-yellow-500/50 max-w-lg w-full">
        <h1 class="text-3xl font-bold text-yellow-500 text-center mb-2">🎮 SEGREDO DOS NÚMEROS</h1>
        <p class="text-center text-gray-400 mb-6">Fase {fase_atual}/4 · Pontos: {pontos_atuais:,}</p>
        {f'<div class="text-center p-4 rounded-lg mb-6 text-lg font-bold {"bg-green-900/50 text-green-400" if "✅" in msg or "🏆" in msg else "bg-red-900/50 text-red-400"}">{msg}</div>' if msg else ''}
        <div class="bg-gray-900 border-2 border-yellow-500/40 rounded-lg p-6 text-center mb-6">
            <p class="text-gray-400 mb-2">Número:</p>
            <p class="text-5xl font-mono text-yellow-400 font-bold tracking-widest">{num_exibicao}</p>
        </div>
        <form method="POST" class="space-y-4">
            <input type="text" name="resposta" placeholder="Digite o inverso..." class="w-full bg-gray-900 border-2 border-yellow-500 rounded-lg text-center text-2xl text-yellow-400 p-3 font-mono" autocomplete="off" required>
            <div class="flex gap-3">
                <button type="submit" class="flex-1 bg-yellow-600 text-black font-bold py-3 rounded-lg text-lg">✅ Decifrar</button>
                <button type="submit" name="acao" value="reiniciar" class="bg-gray-600 text-white px-6 py-3 rounded-lg">🔄 Reiniciar</button>
            </div>
        </form>
        <p class="text-center mt-6"><a href="/plataforma" class="text-yellow-500">← Voltar</a></p>
    </div>
</body>
</html>''')

# --------------------------------------------------
# 🏠 PLATAFORMA PRINCIPAL — REDE SOCIAL + POSTAGENS
# --------------------------------------------------
@app.route("/plataforma", methods=["GET", "POST"])
def plataforma():
    if not usuario_logado():
        return redirect(url_for("inicio"))
    usuario_id = session["usuario_id"]
    
    try:
        pagina = int(request.args.get("pagina", 1))
        if pagina < 1:
            pagina = 1
    except ValueError:
        pagina = 1

    itens_por_pagina = 20
    offset = (pagina - 1) * itens_por_pagina

    # ==================================================
    # 📸 POSTAGEM COM FOTO/VÍDEO — CORRIGIDO
    # ==================================================
    if request.method == "POST":
        texto = request.form.get("texto_post", "").strip()
        arquivo = request.files.get("arquivo")
        url_midia = None

        if arquivo and arquivo.filename:
            if not allowed_file(arquivo.filename):
                return '''
                <div style="background:#0f172a;color:white;min-height:100vh;padding:50px;text-align:center;font-family:Arial;">
                    <h2 style="color:#ef4444;">❌ Tipo de arquivo não permitido</h2>
                    <p style="margin:20px 0;">Use PNG, JPG, JPEG, GIF, MP4, MOV, AVI ou WEBM.</p>
                    <a href="/plataforma" style="color:#f59e0b;font-size:18px;">← Voltar</a>
                </div>
                ''', 400

            extensao = arquivo.filename.rsplit(".", 1)[1].lower()
            nome_seguro = secure_filename(arquivo.filename)
            if not nome_seguro:
                nome_seguro = "midia"
            nome_temporario = f"jobosan_{uuid.uuid4().hex}.{extensao}"
            pasta_temp = "/tmp" if os.path.exists("/tmp") else BASE_DIR
            caminho_temp = os.path.join(pasta_temp, nome_temporario)

            try:
                arquivo.save(caminho_temp)
                if not os.path.exists(caminho_temp) or os.path.getsize(caminho_temp) <= 0:
                    raise Exception("Arquivo vazio ou não salvo")

                extensoes_video = {"mp4", "mov", "avi", "webm"}
                if extensao in extensoes_video:
                    upload_result = cloudinary.uploader.upload_large(
                        caminho_temp,
                        resource_type="video",
                        chunk_size=6000000,
                        folder="jobosan/postagens"
                    )
                else:
                    upload_result = cloudinary.uploader.upload(
                        caminho_temp,
                        resource_type="image",
                        folder="jobosan/postagens"
                    )

                url_midia = upload_result.get("secure_url")
                if not url_midia:
                    raise Exception("URL não retornada")
                print("✅ MÍDIA ENVIADA:", url_midia)

            except Exception as e:
                print("❌ ERRO UPLOAD:", repr(e))
                return f'''
                <div style="background:#0f172a;color:white;min-height:100vh;padding:50px;text-align:center;font-family:Arial;">
                    <h2 style="color:#ef4444;">❌ Erro ao enviar mídia</h2>
                    <p style="color:#cbd5e1;margin:20px 0;">{str(e)}</p>
                    <a href="/plataforma" style="color:#f59e0b;font-size:18px;">← Voltar</a>
                </div>
                ''', 500
            finally:
                if os.path.exists(caminho_temp):
                    try: os.remove(caminho_temp)
                    except: pass

        # Salva no banco
        if texto or url_midia:
            conn = get_db()
            try:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO postagens (usuario_id, texto, arquivo, data_postagem) VALUES (?, ?, ?, ?)",
                    (usuario_id, texto, url_midia, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
            finally:
                conn.close()
            return redirect(url_for("plataforma"))

    # Curtidas
    if "curtir" in request.args:
        pid = request.args.get("curtir")
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO curtidas (usuario_id, postagem_id) VALUES (?, ?)", (usuario_id, pid))
        except sqlite3.IntegrityError:
            c.execute("DELETE FROM curtidas WHERE usuario_id = ? AND postagem_id = ?", (usuario_id, pid))
        conn.commit()
        conn.close()
        return redirect(url_for("plataforma", pagina=pagina) + "#post-" + pid)
    
    # Dados do usuário
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT nome, pontos, dna_chave, email FROM usuarios WHERE id = ?", (usuario_id,))
    usuario_dados = c.fetchone()
    if not usuario_dados:
        conn.close()
        session.clear()
        return redirect(url_for("inicio"))
    nome_usuario, total_pontos, dna_chave, email_usuario = usuario_dados
    
    # Paginação
    c.execute("SELECT COUNT(*) FROM postagens")
    total_posts_banco = c.fetchone()[0]
    total_paginas = (total_posts_banco + itens_por_pagina - 1) // itens_por_pagina or 1

    # Postagens
    c.execute("""SELECT p.id, p.texto, p.arquivo, p.data_postagem, u.nome,
               (SELECT COUNT(*) FROM curtidas c WHERE c.postagem_id = p.id) as total_curtidas,
               EXISTS(SELECT 1 FROM curtidas c WHERE c.postagem_id = p.id AND c.usuario_id = ?) as curtiu
               FROM postagens p JOIN usuarios u ON p.usuario_id = u.id 
               ORDER BY p.data_postagem DESC LIMIT ? OFFSET ?""", (usuario_id, itens_por_pagina, offset))
    postagens = c.fetchall()
    conn.close()
    
    posts_html = ""
    for p in postagens:
        pid, texto, arquivo_url, data, autor, curtidas, curtiu = p
        posts_html += f'''<div id="post-{pid}" class="bg-gray-800 p-4 rounded-lg border border-yellow-500/30 mb-4">
            <h4 class="font-bold text-yellow-400">{autor}</h4><p class="text-sm text-gray-400">{data}</p>
            {f'<p class="my-3 whitespace-pre-wrap">{texto}</p>' if texto else ''}'''
        
        if arquivo_url:
            if any(ext in arquivo_url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif"]) or "/image/upload/" in arquivo_url.lower():
                posts_html += f'<img src="{arquivo_url}" class="max-w-full rounded-lg my-3">'
            else:
                posts_html += f'<video controls class="max-w-full rounded-lg my-3"><source src="{arquivo_url}"></video>'

        posts_html += f'''<div class="mt-3 pt-3 border-t border-gray-700">
            <a href="/plataforma?curtir={pid}&pagina={pagina}#post-{pid}" class="text-{'red' if curtiu else 'gray'}-400">👍 {curtidas} Curtida{'s' if curtidas != 1 else ''}</a>
        </div></div>'''
    
    if not posts_html:
        posts_html = '<p class="text-center text-gray-500 py-10">Ainda não há postagens. Seja o primeiro a compartilhar!</p>'
    
    btn_anterior = f'<a href="/plataforma?pagina={pagina - 1}" class="bg-gray-700 hover:bg-gray-600 text-yellow-400 font-bold px-4 py-2 rounded-lg">← Anterior</a>' if pagina > 1 else '<span class="text-gray-600 bg-gray-800 px-4 py-2 rounded-lg cursor-not-allowed">← Anterior</span>'
    btn_proxima = f'<a href="/plataforma?pagina={pagina + 1}" class="bg-gray-700 hover:bg-gray-600 text-yellow-400 font-bold px-4 py-2 rounded-lg">Próxima →</a>' if pagina < total_paginas else '<span class="text-gray-600 bg-gray-800 px-4 py-2 rounded-lg cursor-not-allowed">Próxima →</span>'

    paginacao_html = f'''<div class="flex justify-between items-center bg-gray-800 p-4 rounded-lg border border-yellow-500/30 my-6">
        {btn_anterior}
        <span class="text-gray-300 font-bold text-sm">Página {pagina} de {total_paginas}</span>
        {btn_proxima}
    </div>'''

    botao_admin = f'<a href="/area_privada" class="bg-red-600 text-white px-4 py-2 rounded-lg text-sm ml-2">🔒 Área Privada</a>' if email_usuario.strip().lower() == EMAIL_DONO.lower() else ""
    
    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plataforma — {NOME_APLICACAO}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>.tab-content{{display:block;}}.tab-content.hidden{{display:none !important;}}</style>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-6">
        <div class="flex flex-wrap justify-between items-center border-b border-gray-700 pb-4 mb-6">
            <div><h1 class="text-2xl font-bold text-yellow-500">⚡ {NOME_APLICACAO}</h1><p class="text-gray-400">Bem-vindo, {nome_usuario}!</p></div>
            <div class="text-right">
                <p class="text-sm text-gray-400">Pontos</p><p class="text-xl font-bold text-yellow-500">{total_pontos}</p>
                <a href="/sair" class="text-red-400 text-sm ml-2">Sair</a> {botao_admin}
            </div>
        </div>
        <div class="flex flex-wrap gap-2 mb-6 border-b border-gray-700 pb-2">
            <button class="tab-btn bg-yellow-600 text-black px-4 py-2 rounded-t-lg font-bold" onclick="switchTab('rede')">Rede Social</button>
            <button class="tab-btn bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-t-lg" onclick="switchTab('jogos')">🎮 Jogos</button>
            <button class="tab-btn bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-t-lg" onclick="switchTab('ia')">🤖 IA</button>
            <button class="tab-btn bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-t-lg" onclick="switchTab('dna')">🧬 DNA</button>
        </div>

        <!-- REDE SOCIAL -->
        <div id="tab-rede" class="tab-content">
            <form method="POST" enctype="multipart/form-data" class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 mb-6">
                <h3 class="text-yellow-500 font-bold mb-3">✍️ Nova Postagem</h3>
                <textarea name="texto_post" rows="3" placeholder="Escreva algo..." class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white mb-3"></textarea>
                <div class="flex flex-col gap-3">
                    <input type="file" name="arquivo" accept="image/*,video/*" class="text-gray-300">
                    <button type="submit" class="bg-yellow-600 text-black font-bold py-2 rounded-lg">📤 Publicar</button>
                </div>
            </form>

            <h3 class="text-yellow-500 font-bold mb-3">📰 Postagens</h3>
            {posts_html}
            {paginacao_html}
        </div>

        <!-- JOGOS -->
        <div id="tab-jogos" class="tab-content hidden">
            <h3 class="text-yellow-500 font-bold mb-4">🎮 Área de Jogos</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <a href="/jogo_bentinho" class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 hover:border-yellow-400 transition">
                    <h4 class="text-xl font-bold text-yellow-400">🎮 Segredo dos Números</h4>
                    <p class="text-gray-400 mt-2">Decifre o número e ganhe pontos!</p>
                </a>
                <a href="/jogo_cartas" class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 hover:border-yellow-400 transition">
                    <h4 class="text-xl font-bold text-yellow-400">🃏 Jogo das Cartas</h4>
                    <p class="text-gray-400 mt-2">Converta as cartas corretamente!</p>
                </a>
            </div>
        </div>

        <!-- IA -->
        <div id="tab-ia" class="tab-content hidden">
            <h3 class="text-yellow-500 font-bold mb-4">🤖 Inteligência Artificial</h3>
            <form action="/responder_ia" method="POST" class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 mb-4">
                <label class="block text-gray-300 mb-2">Pergunte à IA:</label>
                <input type="text" name="pergunta" placeholder="Faça sua pergunta..." class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white mb-3" required>
                <button type="submit" class="bg-yellow-600 text-black font-bold py-2 px-4 rounded-lg">Enviar</button>
            </form>

            <h4 class="text-yellow-400 font-bold mt-6 mb-3">📚 Ensinar a IA</h4>
            <form action="/ensinar_ia" method="POST" class="bg-gray-800 p-5 rounded-lg border border-green-500/30">
                <input type="text" name="pergunta_chave" placeholder="Palavra/Assunto" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white mb-3" required>
                <textarea name="resposta_customizada" rows="4" placeholder="Resposta que a IA deve dar..." class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white mb-3" required></textarea>
                <button type="submit" class="bg-green-600 text-white font-bold py-2 px-4 rounded-lg">💾 Salvar na Memória</button>
            </form>
        </div>

        <!-- DNA -->
        <div id="tab-dna" class="tab-content hidden">
            <h3 class="text-yellow-500 font-bold mb-4">🧬 Sua Chave DNA — ÚNICA</h3>
            <div class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30">
                <p class="text-gray-400 mb-2">Esta é sua identidade permanente na plataforma:</p>
                <div class="bg-gray-900 p-4 rounded-lg border border-yellow-500/50 font-mono text-yellow-400 text-sm break-all">
                    {dna_chave}
                </div>
                <p class="text-gray-500 text-sm mt-3">Guarde bem! É sua assinatura exclusiva.</p>
            </div>
        </div>
    </div>

    <script>
        function switchTab(nome) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => {{
                b.classList.remove('bg-yellow-600', 'text-black');
                b.classList.add('bg-gray-700');
            }});
            document.getElementById('tab-' + nome).classList.remove('hidden');
            event.target.classList.remove('bg-gray-700');
            event.target.classList.add('bg-yellow-600', 'text-black');
        }}
    </script>
</body>
</html>''')

# ==================================================
# ✅ PORTA 5000 — FINALIZAÇÃO
# ==================================================
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)
