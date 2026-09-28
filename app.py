from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, render_template_string, flash, jsonify
import hashlib
import os
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("CHAVE_SECRETA", "JOBOSAN_REDE_2026_SEGURA")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=3650)

NOME_APP = "Jobosan Rede Social"
BANCO_ARQUIVO = "jobosan_rede.db"

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
        CREATE TABLE IF NOT EXISTS curtidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            postagem_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (postagem_id) REFERENCES postagens(id)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ==============================================
# TEMPLATES — TUDO AQUI DENTRO, SEM ARQUIVOS EXTERNOS
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
    </style>
</head>
<body>
    <div class="cabecalho">
        <h1>🚀 Jobosan Rede Social</h1>
        {% if session.usuario_id %}
            <p>Bem-vindo, {{ session.nome }}! | 
            <a href="{{ url_for('inicio') }}">Início</a> | 
            <a href="{{ url_for('sair') }}">Sair</a></p>
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
<form method="post" enctype="multipart/form-data">
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
            {% if p.midia.endswith(('.jpg','.jpeg','.png','.gif')) %}
                <img src="{{ p.midia }}" alt="mídia">
            {% else %}
                <video controls><source src="{{ p.midia }}">Seu navegador não suporta vídeo</video>
            {% endif %}
        {% endif %}
    </div>
{% else %}
    <p style="text-align:center; color:#666;">Nenhuma publicação ainda. Seja o primeiro a postar!</p>
{% endfor %}
""")

# ==============================================
# ROTAS
# ==============================================
@app.route("/")
def inicio():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    
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
            c.execute("INSERT INTO usuarios (nome, email, senha, data_cadastro) VALUES (?, ?, ?, ?)",
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
        c.execute("SELECT id, nome FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))
        usuario = c.fetchone()
        conn.close()
        
        if usuario:
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
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
            import uuid
            ext = arq.filename.rsplit(".", 1)[-1].lower()
            nome_arq = f"{uuid.uuid4().hex}.{ext}"
            pasta = "midias"
            os.makedirs(pasta, exist_ok=True)
            caminho = os.path.join(pasta, nome_arq)
            arq.save(caminho)
            midia_url = f"/{pasta}/{nome_arq}"
    
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
    
    flash("Publicado com sucesso! ✅", "sucesso")
    return redirect(url_for("inicio"))

@app.route("/midias/<nome>")
def servir_midia(nome):
    from flask import send_from_directory
    return send_from_directory("midias", nome)

# ==============================================
# INICIAR SERVIDOR
# ==============================================
if __name__ == "__main__":
    print("="*50)
    print("🚀 JOBOSAN REDE SOCIAL — INICIANDO...")
    print("✅ Banco de dados:", BANCO_ARQUIVO)
    print("✅ Porta: 5000")
    print("="*50)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
