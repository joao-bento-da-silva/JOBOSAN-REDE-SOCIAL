from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, render_template_string, flash, send_from_directory
import hashlib
import os
import random
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("CHAVE_SECRETA", "JOBOSAN_REDE_2026_SEGURA")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=3650)

BANCO_ARQUIVO = "jobosan_rede.db"
PASTA_MIDIAS = "midias"
os.makedirs(PASTA_MIDIAS, exist_ok=True)
LETRAS_DNA = ['T', 'C', 'G', 'A']

def gerar_chave_dna(tamanho=32):
    return ''.join(random.choice(LETRAS_DNA) for _ in range(tamanho))

def get_db():
    conn = sqlite3.connect(BANCO_ARQUIVO)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            pontos INTEGER DEFAULT 0,
            dna_chave TEXT UNIQUE,
            data_cadastro TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS postagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            texto TEXT,
            midia_url TEXT,
            data_postagem TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS jogadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo_jogo TEXT NOT NULL,
            acertou INTEGER,
            pontos_ganhos INTEGER DEFAULT 0,
            data_hora TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

BASE_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ titulo }} — Jobosan</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#12122f;padding:20px}
.container{max-width:600px;margin:0 auto}
.topo{background:linear-gradient(135deg,#000033,#1a1a50);color:#fff;padding:20px;text-align:center;border-radius:10px;margin-bottom:20px;border:2px solid #f5b800}
.menu{display:flex;gap:8px;flex-wrap:wrap;margin:15px 0;justify-content:center}
.menu a{flex:1;min-width:90px;text-align:center;padding:10px;background:#2a2a4a;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;font-size:14px}
.menu a.ativo{background:#f5b800;color:#000}
.caixa{background:#fff;padding:20px;border-radius:10px;margin-bottom:15px;box-shadow:0 2px 8px rgba(0,0,0,0.2)}
.caixa-dna{background:linear-gradient(135deg,#1a1a3a,#2a2a5a);color:#fff;padding:25px;border-radius:12px;border:2px solid #f5b800}
.chave-dna{background:#000;color:#f5b800;font-family:monospace;font-size:16px;padding:15px;border-radius:8px;word-break:break-all;margin:15px 0;letter-spacing:1px}
input,textarea,button{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:6px;font-size:16px}
button{background:#1a73e8;color:#fff;border:none;cursor:pointer;font-weight:bold}
.postagem{border-bottom:1px solid #eee;padding:15px 0}
.autor{font-weight:bold;color:#1a73e8}
.data{color:#888;font-size:12px}
.msg{padding:10px;margin:10px 0;border-radius:6px}
.sucesso{background:#d4edda;color:#155724}
.erro{background:#f8d7da;color:#721c24}
img,video{max-width:100%;border-radius:8px;margin:10px 0}
h2{color:#fff;margin-bottom:15px}
h3{color:#000;margin-bottom:10px}
</style>
</head>
<body>
<div class="container">
<div class="topo">
<h1>🚀 Jobosan</h1>
{% if session.usuario_id %}
<p>Bem-vindo, {{ session.nome }}! 🏆 Pontos: {{ session.pontos }}</p>
<div class="menu">
<a href="{{ url_for('inicio') }}" {% if pagina=='inicio' %}class="ativo"{% endif %}>Rede Social</a>
<a href="{{ url_for('jogos') }}" {% if pagina=='jogos' %}class="ativo"{% endif %}>🃏 Jogos</a>
<a href="{{ url_for('dna') }}" {% if pagina=='dna' %}class="ativo"{% endif %}>🧬 DNA</a>
<a href="{{ url_for('sair') }}">Sair</a>
</div>
{% else %}
<p><a href="{{ url_for('entrar') }}" style="color:#fff">Entrar</a> | <a href="{{ url_for('cadastrar') }}" style="color:#fff">Cadastrar</a></p>
{% endif %}
</div>
{% with msgs = get_flashed_messages(with_categories=true) %}
{% if msgs %}
{% for cat, msg in msgs %}
<div class="msg {{ cat }}">{{ msg }}</div>
{% endfor %}
{% endif %}
{% endwith %}
{% block conteudo %}{% endblock %}
</div>
</body>
</html>
"""

@app.route("/")
def inicio():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT p.id, p.texto, p.midia_url as midia, p.data_postagem as data, u.nome FROM postagens p JOIN usuarios u ON p.usuario_id = u.id ORDER BY p.id DESC")
    posts = c.fetchall()
    conn.close()
    bloco = """
<h2>📢 Postar Algo</h2>
<div class="caixa">
<form method="post" enctype="multipart/form-data">
<textarea name="texto" placeholder="Escreva algo..." rows="4"></textarea>
<input type="file" name="midia" accept="image/*,video/*">
<button type="submit" formaction="/postar">Publicar</button>
</form>
</div>
<h2>📰 Publicações</h2>
{% if posts %}
{% for p in posts %}
<div class="caixa postagem">
<span class="autor">{{ p.nome }}</span> <span class="data">{{ p.data }}</span>
{% if p.texto %}<p style="margin:10px 0;color:#333">{{ p.texto }}</p>{% endif %}
{% if p.midia %}
{% set ext = p.midia.split('.')[-1].lower() %}
{% if ext in ['jpg','jpeg','png','gif'] %}
<img src="{{ p.midia }}" alt="mídia">
{% else %}
<video controls style="width:100%;border-radius:8px"><source src="{{ p.midia }}">Seu navegador não suporta vídeo.</video>
{% endif %}
{% endif %}
</div>
{% endfor %}
{% else %}
<p style="text-align:center;color:#ccc;">Nenhuma publicação ainda. Seja o primeiro a postar!</p>
{% endif %}
"""
    return render_template_string(BASE_HTML.replace("{% block conteudo %}{% endblock %}", bloco), titulo="Início", posts=posts, pagina="inicio")

@app.route("/entrar", methods=["GET","POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        senha = request.form.get("senha","")
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, nome, pontos FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))
        usr = c.fetchone()
        conn.close()
        if usr:
            session["usuario_id"] = usr["id"]
            session["nome"] = usr["nome"]
            session["pontos"] = usr["pontos"]
            flash(f"Bem-vindo, {usr['nome']}!", "sucesso")
            return redirect(url_for("inicio"))
        else:
            flash("E-mail ou senha incorretos!", "erro")
    bloco = """
<div class="caixa">
<h3 style="text-align:center">🔐 Entrar</h3>
<form method="post">
<label>E-mail:</label>
<input type="email" name="email" required>
<label>Senha:</label>
<input type="password" name="senha" required>
<button type="submit">Entrar</button>
</form>
<p style="text-align:center;margin-top:10px">Não tem conta? <a href="{{ url_for('cadastrar') }}">Cadastre-se</a></p>
</div>
"""
    return render_template_string(BASE_HTML.replace("{% block conteudo %}{% endblock %}", bloco), titulo="Entrar")

@app.route("/cadastrar", methods=["GET","POST"])
def cadastrar():
    if request.method == "POST":
        nome = request.form.get("nome","").strip()
        email = request.form.get("email","").strip().lower()
        senha = request.form.get("senha","")
        if not nome or not email or len(senha) < 4:
            flash("Preencha todos os campos (senha com 4+ caracteres)", "erro")
        else:
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            chave_dna = gerar_chave_dna(32)
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT INTO usuarios (nome,email,senha,dna_chave,data_cadastro,pontos) VALUES (?,?,?,?,?,0)",
                         (nome,email,senha_hash,chave_dna,agora))
                conn.commit()
                conn.close()
                flash("Conta criada! Faça login.", "sucesso")
                return redirect(url_for("entrar"))
            except sqlite3.IntegrityError:
                flash("Este e-mail já está cadastrado!", "erro")
    bloco = """
<div class="caixa">
<h3 style="text-align:center">📝 Criar Conta</h3>
<form method="post">
<label>Nome:</label>
<input type="text" name="nome" required>
<label>E-mail:</label>
<input type="email" name="email" required>
<label>Senha:</label>
<input type="password" name="senha" required>
<button type="submit">Cadastrar</button>
</form>
<p style="text-align:center;margin-top:10px">Já tem conta? <a href="{{ url_for('entrar') }}">Entre</a></p>
</div>
"""
    return render_template_string(BASE_HTML.replace("{% block conteudo %}{% endblock %}", bloco), titulo="Cadastrar")

@app.route("/sair")
def sair():
    session.clear()
    flash("Você saiu com sucesso!", "sucesso")
    return redirect(url_for("entrar"))

@app.route("/postar", methods=["POST"])
def postar():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    texto = request.form.get("texto","").strip()
    midia_url = ""
    if "midia" in request.files:
        arq = request.files["midia"]
        if arq.filename:
            ext = arq.filename.rsplit(".",1)[-1].lower()
            nome_arq = f"{uuid.uuid4().hex}.{ext}"
            caminho = os.path.join(PASTA_MIDIAS, nome_arq)
            arq.save(caminho)
            midia_url = f"/midias/{nome_arq}"
    if not texto and not midia_url:
        flash("Escreva algo ou envie uma imagem/vídeo!", "erro")
        return redirect(url_for("inicio"))
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO postagens (usuario_id,texto,midia_url,data_postagem) VALUES (?,?,?,?)",
             (session["usuario_id"], texto, midia_url, agora))
    conn.commit()
    conn.close()
    flash("✅ Publicado!", "sucesso")
    return redirect(url_for("inicio"))

@app.route("/midias/<nome>")
def midias(nome):
    return send_from_directory(PASTA_MIDIAS, nome)

@app.route("/jogos", methods=["GET","POST"])
def jogos():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    res_carta = ""
    res_num = ""
    acertou_carta = False
    pts_carta = 0
    acertou_num = False
    pts_num = 0
    if request.method == "POST":
        if "chute_carta" in request.form:
            chute = int(request.form.get("chute_carta",0))
            carta = random.randint(1,13)
            if chute == carta:
                acertou_carta = True
                pts_carta = 10
                res_carta = f"🎉 Acertou! A carta era {carta}!"
            else:
                res_carta = f"❌ Errou! A carta era {carta}."
            if acertou_carta:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (pts_carta, session["usuario_id"]))
                c.execute("INSERT INTO jogadas (usuario_id,tipo_jogo,acertou,pontos_ganhos,data_hora) VALUES (?,?,1,?,?)",
                         (session["usuario_id"],"cartas",pts_carta,datetime.now().strftime("%d/%m/%Y %H:%M")))
                conn.commit()
                c.execute("SELECT pontos FROM usuarios WHERE id = ?", (session["usuario_id"],))
                session["pontos"] = c.fetchone()["pontos"]
                conn.close()
        if "chute_num" in request.form:
            if "segredo_num" not in session:
                session["segredo_num"] = random.randint(1,100)
            chute = int(request.form.get("chute_num",0))
            segredo = session["segredo_num"]
            if chute == segredo:
                acertou_num = True
                pts_num = 15
                res_num = f"🎉 Acertou! O número era {segredo}!"
                session.pop("segredo_num", None)
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (pts_num, session["usuario_id"]))
                c.execute("INSERT INTO jogadas (usuario_id,tipo_jogo,acertou,pontos_ganhos,data_hora) VALUES (?,?,1,?,?)",
                         (session["usuario_id"],"numero",pts_num,datetime.now().strftime("%d/%m/%Y %H:%M")))
                conn.commit()
                c.execute("SELECT pontos FROM usuarios WHERE id = ?", (session["usuario_id"],))
                session["pontos"] = c.fetchone()["pontos"]
                conn.close()
            elif chute < segredo:
                res_num = "🔼 O número é MAIOR!"
            else:
                res_num = "🔽 O número é MENOR!"
    bloco = f"""
<h2>🃏 Jogos</h2>
<div class="caixa">
<h3>Adivinhe a carta (1 a 13)</h3>
<form method="post">
<input type="number" name="chute_carta" min="1" max="13" placeholder="Seu palpite" required>
<button type="submit">Jogar Carta</button>
</form>
{res_carta}
{('<p style="color:green;font-weight:bold">+10 pontos!</p>' if acertou_carta else '')}
</div>
<div class="caixa">
<h3>🔢 Adivinhe o número (1 a 100)</h3>
<form method="post">
<input type="number" name="chute_num" min="1" max="100" placeholder="Seu palpite" required>
<button type="submit">Jogar Número</button>
</form>
{res_num}
{('<p style="color:green;font-weight:bold">+15 pontos!</p>' if acertou_num else '')}
</div>
"""
    return render_template_string(BASE_HTML.replace("{% block conteudo %}{% endblock %}", bloco), titulo="Jogos", pagina="jogos")

@app.route("/dna")
def dna():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT dna_chave FROM usuarios WHERE id = ?", (session["usuario_id"],))
    res = c.fetchone()
    if not res or not res["dna_chave"]:
        chave = gerar_chave_dna(32)
        c.execute("UPDATE usuarios SET dna_chave = ? WHERE id = ?", (chave, session["usuario_id"]))
        conn.commit()
        chave_dna = chave
    else:
        chave_dna = res["dna_chave"]
    conn.close()
    bloco = f"""
<h2 style="text-align:center">🧬 Sua Chave DNA — ÚNICA</h2>
<div class="caixa-dna">
<p style="font-size:16px;opacity:0.9">Esta é sua identidade permanente na plataforma:</p>
<div class="chave-dna">{chave_dna}</div>
<p style="font-size:14px;opacity:0.7;margin-top:10px">Guarde bem! É sua assinatura exclusiva.<br>Letras: <strong>T - C - G - A</strong></p>
</div>
"""
    return render_template_string(BASE_HTML.replace("{% block conteudo %}{% endblock %}", bloco), titulo="Chave DNA", pagina="dna")

if __name__ == "__main__":
    print("="*50)
    print("🧬 JOBOSAN — REDE SOCIAL + JOGOS + DNA")
    print("✅ Banco:", BANCO_ARQUIVO)
    print("✅ Mídias:", PASTA_MIDIAS)
    print("✅ DNA: T-C-G-A — Chaves únicas")
    print("✅ Porta: 5000")
    print("="*50)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
