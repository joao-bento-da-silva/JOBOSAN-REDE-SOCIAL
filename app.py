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

NOME_APP = "Jobosan Rede Social"
BANCO_ARQUIVO = "jobosan_rede.db"
PASTA_MIDIAS = "midias"
os.makedirs(PASTA_MIDIAS, exist_ok=True)

# ==============================================
# BANCO DE DADOS
# ==============================================
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

# ==============================================
# TEMPLATES
# ==============================================
TPL_BASE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titulo }} — Jobosan</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:Arial, sans-serif; }
        body { background:#f0f2f5; padding:20px; }
        .container { max-width:600px; margin:0 auto; }
        .cabecalho { background:#1a73e8; color:white; padding:20px; text-align:center; border-radius:10px; margin-bottom:20px; }
        .cabecalho a { color:white; text-decoration:none; margin:0 10px; }
        .caixa { background:white; padding:20px; border-radius:10px; margin-bottom:15px; box-shadow:0 2px 5px rgba(0,0,0,0.1); }
        input, textarea, button { width:100%; padding:12px; margin:8px 0; border:1px solid #ddd; border-radius:6px; font-size:16px; }
        button { background:#1a73e8; color:white; border:none; cursor:pointer; font-weight:bold; }
        button:hover { background:#1557b0; }
        .postagem { border-bottom:1px solid #eee; padding:15px 0; }
        .autor { font-weight:bold; color:#1a73e8; }
        .data { color:#888; font-size:12px; }
        .mensagem { padding:10px; margin:10px 0; border-radius:6px; }
        .sucesso { background:#d4edda; color:#155724; }
        .erro { background:#f8d7da; color:#721c24; }
        img, video { max-width:100%; border-radius:8px; margin:10px 0; }
        .menu { display:flex; gap:10px; flex-wrap:wrap; margin:15px 0; }
        .menu a { flex:1; min-width:120px; text-align:center; padding:10px; background:#e8f0fe; color:#1a73e8; border-radius:6px; text-decoration:none; font-weight:bold; }
        .menu a:hover { background:#d2e3fc; }
        .carta { display:inline-block; width:60px; height:90px; line-height:90px; text-align:center; border:2px solid #1a73e8; border-radius:8px; font-size:24px; font-weight:bold; margin:5px; background:white; }
    </style>
</head>
<body>
    <div class="cabecalho">
        <h1>🚀 Jobosan Rede Social</h1>
        {% if session.usuario_id %}
            <p>Bem-vindo, {{ session.nome }}! 🏆 Pontos: {{ session.pontos }}</p>
            <div class="menu">
                <a href="{{ url_for('inicio') }}">Início</a>
                <a href="{{ url_for('jogo_cartas') }}">🃏 Cartas</a>
                <a href="{{ url_for('jogo_numero') }}">🔢 Segredo</a>
                <a href="{{ url_for('sair') }}">Sair</a>
            </div>
        {% else %}
            <p><a href="{{ url_for('entrar') }}">Entrar</a> | 
            <a href="{{ url_for('cadastrar') }}">Cadastrar</a></p>
        {% endif %}
    </div>
    <div class="container">
        {% with mensagens = get_flashed_messages(with_categories=true) %}
            {% if mensagens %}
                {% for cat, msg in mensagens %}
                    <div class="mensagem {{ cat }}">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% block conteudo %}{% endblock %}
    </div>
</body>
</html>
"""

TPL_LOGIN = TPL_BASE.replace("{% block conteudo %}{% endblock %}", """
<h2>🔐 Entrar</h2>
<form method="post">
    <label>E-mail:</label>
    <input type="email" name="email" required>
    <label>Senha:</label>
    <input type="password" name="senha" required>
    <button type="submit">Entrar</button>
</form>
<p>Não tem conta? <a href="{{ url_for('cadastrar') }}">Cadastre-se</a></p>
""")

TPL_CADASTRO = TPL_BASE.replace("{% block conteudo %}{% endblock %}", """
<h2>📝 Criar Conta</h2>
<form method="post">
    <label>Nome:</label>
    <input type="text" name="nome" required>
    <label>E-mail:</label>
    <input type="email" name="email" required>
    <label>Senha:</label>
    <input type="password" name="senha" required>
    <button type="submit">Cadastrar</button>
</form>
<p>Já tem conta? <a href="{{ url_for('entrar') }}">Entre</a></p>
""")

TPL_INICIO = TPL_BASE.replace("{% block conteudo %}{% endblock %}", """
<h2>📢 Postar Algo</h2>
<form action="{{ url_for('postar') }}" method="post" enctype="multipart/form-data">
    <textarea name="texto" placeholder="Escreva algo..." rows="4"></textarea>
    <input type="file" name="midia" accept="image/*,video/*">
    <button type="submit">Publicar</button>
</form>

<h2 style="margin-top:30px;">📰 Publicações</h2>
{% for p in postagens %}
    <div class="caixa postagem">
        <span class="autor">{{ p.nome }}</span>
        <span class="data">{{ p.data }}</span>
        {% if p.texto %}<p style="margin:10px 0;">{{ p.texto }}</p>{% endif %}
        {% if p.midia %}
            {% set ext = p.midia.split('.')[-1].lower() %}
            {% if ext in ['jpg','jpeg','png','gif'] %}
                <img src="{{ p.midia }}" alt="mídia">
            {% else %}
                <video controls style="width:100%; border-radius:8px;">
                    <source src="{{ p.midia }}">
                    Seu navegador não suporta vídeo.
                </video>
            {% endif %}
        {% endif %}
    </div>
{% else %}
    <p style="text-align:center; color:#666;">Nenhuma publicação ainda. Seja o primeiro a postar!</p>
{% endfor %}
""")

TPL_CARTAS = TPL_BASE.replace("{% block conteudo %}{% endblock %}", """
<h2>🃏 Jogo das Cartas</h2>
<p>Adivinhe a carta! 1 a 13</p>
<form method="post">
    <input type="number" name="chute" min="1" max="13" placeholder="Seu palpite" required>
    <button type="submit">Jogar</button>
</form>
{% if resultado %}
<div class="caixa">
    <p>{{ resultado }}</p>
    {% if acertou %}<p>🎉 Ganhou {{ pontos }} pontos!</p>{% endif %}
</div>
{% endif %}
""")

TPL_NUMERO = TPL_BASE.replace("{% block conteudo %}{% endblock %}", """
<h2>🔢 Segredo dos Números</h2>
<p>Adivinhe o número entre 1 e 100!</p>
<form method="post">
    <input type="number" name="chute" min="1" max="100" placeholder="Seu palpite" required>
    <button type="submit">Tentar</button>
</form>
{% if dica %}
<div class="caixa">
    <p>{{ dica }}</p>
    {% if acertou %}<p>🎉 Acertou! +{{ pontos }} pontos!</p>{% endif %}
</div>
{% endif %}
""")

# ==============================================
# FUNÇÃO ATUALIZAR PONTOS NA SESSÃO
# ==============================================
def atualizar_pontos_sessao(usuario_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT pontos FROM usuarios WHERE id = ?", (usuario_id,))
    res = c.fetchone()
    conn.close()
    if res:
        session["pontos"] = res["pontos"]

# ==============================================
# ROTAS
# ==============================================
@app.route("/")
def inicio():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    atualizar_pontos_sessao(session["usuario_id"])
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.texto, p.midia_url as midia, p.data_postagem as data, u.nome
        FROM postagens p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.id DESC
    """)
    postagens = c.fetchall()
    conn.close()
    
    return render_template_string(TPL_INICIO, titulo="Início", postagens=postagens)

@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        if not nome or not email or len(senha) < 4:
            flash("Preencha todos os campos (senha com 4+ caracteres)", "erro")
            return render_template_string(TPL_CADASTRO, titulo="Cadastrar")
        
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (nome, email, senha, data_cadastro, pontos) VALUES (?, ?, ?, ?, 0)",
                     (nome, email, senha_hash, agora))
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso! Faça login.", "sucesso")
            return redirect(url_for("entrar"))
        except sqlite3.IntegrityError:
            flash("Este e-mail já está cadastrado!", "erro")
    
    return render_template_string(TPL_CADASTRO, titulo="Cadastrar")

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, nome, pontos FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))
        usuario = c.fetchone()
        conn.close()
        
        if usuario:
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["pontos"] = usuario["pontos"]
            flash(f"Bem-vindo, {usuario['nome']}!", "sucesso")
            return redirect(url_for("inicio"))
        else:
            flash("E-mail ou senha incorretos!", "erro")
    
    return render_template_string(TPL_LOGIN, titulo="Entrar")

@app.route("/sair")
def sair():
    session.clear()
    flash("Você saiu com sucesso!", "sucesso")
    return redirect(url_for("entrar"))

@app.route("/postar", methods=["POST"])
def postar():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    
    texto = request.form.get("texto", "").strip()
    midia_url = ""
    
    if "midia" in request.files:
        arq = request.files["midia"]
        if arq.filename:
            ext = arq.filename.rsplit(".", 1)[-1].lower()
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
    c.execute("INSERT INTO postagens (usuario_id, texto, midia_url, data_postagem) VALUES (?, ?, ?, ?)",
             (session["usuario_id"], texto, midia_url, agora))
    conn.commit()
    conn.close()
    
    flash("✅ Publicado com sucesso!", "sucesso")
    return redirect(url_for("inicio"))

@app.route("/midias/<nome>")
def servir_midia(nome):
    return send_from_directory(PASTA_MIDIAS, nome)

@app.route("/jogo-cartas", methods=["GET", "POST"])
def jogo_cartas():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    
    resultado = ""
    acertou = False
    pontos_ganhos = 0
    
    if request.method == "POST":
        chute = int(request.form.get("chute", 0))
        carta = random.randint(1, 13)
        
        if chute == carta:
            acertou = True
            pontos_ganhos = 10
            resultado = f"🎉 A carta era {carta}! Acertou!"
        else:
            resultado = f"❌ A carta era {carta}. Tente de novo!"
        
        if acertou:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (pontos_ganhos, session["usuario_id"]))
            c.execute("INSERT INTO jogadas (usuario_id, tipo_jogo, acertou, pontos_ganhos, data_hora) VALUES (?, ?, 1, ?, ?)",
                     (session["usuario_id"], "cartas", pontos_ganhos, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            conn.close()
            atualizar_pontos_sessao(session["usuario_id"])
    
    return render_template_string(TPL_CARTAS, titulo="Jogo das Cartas", resultado=resultado, acertou=acertou, pontos=pontos_ganhos)

@app.route("/jogo-numero", methods=["GET", "POST"])
def jogo_numero():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    
    dica = ""
    acertou = False
    pontos_ganhos = 0
    
    if "segredo" not in session:
        session["segredo"] = random.randint(1, 100)
    
    if request.method == "POST":
        chute = int(request.form.get("chute", 0))
        segredo = session["segredo"]
        
        if chute == segredo:
            acertou = True
            pontos_ganhos = 15
            dica = f"🎉 PARABÉNS! O número era {segredo}! Acertou!"
            session.pop("segredo", None)
            if acertou:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (pontos_ganhos, session["usuario_id"]))
                c.execute("INSERT INTO jogadas (usuario_id, tipo_jogo, acertou, pontos_ganhos, data_hora) VALUES (?, ?, 1, ?, ?)",
                         (session["usuario_id"], "numero", pontos_ganhos, datetime.now().strftime("%d/%m/%Y %H:%M")))
                conn.commit()
                conn.close()
                atualizar_pontos_sessao(session["usuario_id"])
        elif chute < segredo:
            dica = "🔼 O número é MAIOR!"
        else:
            dica = "🔽 O número é MENOR!"
    
    return render_template_string(TPL_NUMERO, titulo="Segredo dos Números", dica=dica, acertou=acertou, pontos=pontos_ganhos)

# ==============================================
# INICIAR SERVIDOR
# ==============================================
if __name__ == "__main__":
    print("="*50)
    print("🚀 JOBOSAN — REDE SOCIAL + JOGOS COMPLETA")
    print("✅ Banco:", BANCO_ARQUIVO)
    print("✅ Mídias:", PASTA_MIDIAS)
    print("✅ Porta: 5000")
    print("="*50)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
