import os
import sqlite3
import secrets
from datetime import timedelta
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, Response
from flask import (
    Flask, render_template_string, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

app = Flask(__name__)

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "jobosan_jogos.db")
)

@app.route('/google510f4f340be76af9.html')
def google_verification():
    return "google-site-verification: google510f4f340be76af9.html"

@app.route('/robots.txt')
def robots():
    content = """User-agent: *
Allow: /
Sitemap: https://jobosan.onrender.com/sitemap.xml
"""
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://jobosan.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return Response(xml_content, mimetype='application/xml')

def agora():
    return datetime.now(timezone.utc).isoformat()

def conectar():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    pasta = os.path.dirname(DATABASE_PATH)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progresso (
                usuario_id INTEGER PRIMARY KEY,
                pontos INTEGER NOT NULL DEFAULT 0,
                fases_concluidas INTEGER NOT NULL DEFAULT 0,
                partidas INTEGER NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                conteudo TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)

inicializar_banco()

def login_obrigatorio(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("entrar"))
        return fn(*args, **kwargs)
    return wrapper

LAYOUT_GERAL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="JOBOSAN - Rede Social e Plataforma Digital criada por João Bento da Silva.">
    <meta name="author" content="João Bento da Silva">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #f0f0f0; margin: 0; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }
        header { background: #1f1f1f; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; }
        header h1 { margin: 0; font-size: 1.5rem; color: #ffcc00; }
        nav a, nav button { color: #fff; background: #333; border: none; padding: 8px 15px; margin-left: 10px; border-radius: 4px; text-decoration: none; cursor: pointer; }
        nav a:hover, nav button:hover { background: #555; }
        .container { flex: 1; max-width: 950px; margin: 20px auto; padding: 20px; background: #1e1e1e; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); width: 92%; }
        footer { text-align: center; padding: 15px; background: #1a1a1a; color: #888; font-size: 0.85rem; border-top: 1px solid #333; }
        .flashes { margin-bottom: 15px; }
        .flash { padding: 10px; border-radius: 4px; margin-bottom: 5px; font-size: 0.9rem; }
        .flash.erro { background: #800000; color: #fff; }
        .flash.sucesso { background: #006600; color: #fff; }
        .auth-container { max-width: 400px; margin: 40px auto; }
        .campo { margin-bottom: 15px; }
        .campo label { display: block; margin-bottom: 5px; color: #ccc; }
        .campo input, .campo textarea { width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #444; color: #fff; border-radius: 4px; box-sizing: border-box; }
        .btn-submit { background: #0275d8; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .btn-submit:hover { background: #025aa5; }
        .auth-footer { text-align: center; margin-top: 15px; font-size: 0.9rem; }
        .auth-footer a { color: #5bc0de; text-decoration: none; }
        .post-card { background: #252525; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #ffcc00; }
        .post-autor { font-weight: bold; color: #ffcc00; margin-bottom: 5px; }
        .post-data { font-size: 0.75rem; color: #888; margin-bottom: 10px; }
    </style>
</head>
<body>
    <header>
        <h1>🌐 JOBOSAN</h1>
        <nav>
            {% if session.get('usuario_id') %}
                <span>Olá, <strong>{{ session.get('usuario_nome') }}</strong></span>
                <a href="{{ url_for('painel') }}">Painel / Feed</a>
                <form action="{{ url_for('sair') }}" method="POST" style="display:inline;">
                    <button type="submit">Sair</button>
                </form>
            {% else %}
                <a href="{{ url_for('entrar') }}">Entrar</a>
                <a href="{{ url_for('cadastro') }}">Criar Conta</a>
            {% endif %}
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flashes">
                    {% for cat, msg in messages %}
                        <div class="flash {{ cat }}">{{ msg }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        {{ content | safe }}
    </main>

    <footer>
        <p>&copy; 2026 JOBOSAN — Criado e Desenvolvido por <strong>João Bento da Silva</strong>. Todos os direitos reservados.</p>
    </footer>
</body>
</html>
"""

REGISTRO_HTML = """
<div class="auth-container">
    <h2>Criar Conta</h2>
    <form method="POST">
        <div class="campo">
            <label for="nome">Nome</label>
            <input type="text" id="nome" name="nome" required>
        </div>
        <div class="campo">
            <label for="email">E-mail</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="campo">
            <label for="senha">Senha (mínimo 6 dígitos)</label>
            <input type="password" id="senha" name="senha" required>
        </div>
        <button type="submit" class="btn-submit">Cadastrar</button>
    </form>
    <div class="auth-footer">
        <p>Já tem uma conta? <a href="{{ url_for('entrar') }}">Entrar</a></p>
    </div>
</div>
"""

LOGIN_HTML = """
<div class="auth-container">
    <h2>Entrar</h2>
    <form method="POST">
        <div class="campo">
            <label for="email">E-mail</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="campo">
            <label for="senha">Senha</label>
            <input type="password" id="senha" name="senha" required>
        </div>
        <button type="submit" class="btn-submit">Entrar</button>
    </form>
    <div class="auth-footer">
        <p>Não tem uma conta? <a href="{{ url_for('cadastro') }}">Criar Conta</a></p>
    </div>
</div>
"""

@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("painel"))
    conteudo = """
    <div style="text-align: center; padding: 30px;">
        <h2>🌐 Bem-vindo à Rede Social JOBOSAN</h2>
        <p style="font-style: italic; color: #ffcc00; margin: 15px 0;">"Conectando ideias e pessoas."</p>
        <div style="margin-top: 25px;">
            <a href=""" + url_for('cadastro') + """ style="background: #5cb85c; color: #fff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">Criar Conta</a>
            <a href=""" + url_for('entrar') + """ style="background: #0275d8; color: #fff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Entrar</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="JOBOSAN", content=conteudo)

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        with conectar() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            
        if user and check_password_hash(user["senha_hash"], senha):
            session.permanent = True
            session["usuario_id"] = user["id"]
            session["usuario_nome"] = user["nome"]
            return redirect(url_for("painel"))
        else:
            flash("E-mail ou senha incorretos.", "erro")
            
    return render_template_string(LAYOUT_GERAL, title="Entrar — JOBOSAN", content=LOGIN_HTML)

@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("index"))

@app.route("/painel", methods=["GET", "POST"])
@login_obrigatorio
def painel():
    if request.method == "POST":
        conteudo_post = request.form.get("conteudo", "").strip()
        if len(conteudo_post) > 0:
            with conectar() as conn:
                conn.execute(
                    "INSERT INTO posts (usuario_id, conteudo, criado_em) VALUES (?, ?, ?)",
                    (session["usuario_id"], conteudo_post, agora())
                )
            flash("Postagem realizada com sucesso!", "sucesso")
        else:
            flash("O post não pode estar vazio.", "erro")
        return redirect(url_for("painel"))

    with conectar() as conn:
        posts = conn.execute("""
            SELECT posts.*, usuarios.nome as autor_nome 
            FROM posts 
            JOIN usuarios ON posts.usuario_id = usuarios.id 
            ORDER BY posts.id DESC
        """).fetchall()

    lista_posts_html = ""
    for p in posts:
        lista_posts_html += f"""
        <div class="post-card">
            <div class="post-autor">👤 {p['autor_nome']}</div>
            <div class="post-data">🕒 {p['criado_em'][:19].replace('T', ' ')}</div>
            <div>{p['conteudo']}</div>
        </div>
        """

    if not lista_posts_html:
        lista_posts_html = "<p style='color: #888; text-align: center;'>Ainda não há postagens. Seja o primeiro a publicar algo!</p>"

    conteudo = f"""
    <div>
        <h2>Feed da Rede Social — JOBOSAN</h2>
        
        <div style="background: #252525; padding: 20px; border-radius: 6px; margin-bottom: 25px;">
            <h3 style="margin-top: 0; color: #ffcc00;">O que você está pensando?</h3>
            <form method="POST">
                <div class="campo">
                    <textarea name="conteudo" rows="3" placeholder="Escreva sua postagem aqui..." required></textarea>
                </div>
                <button type="submit" class="btn-submit" style="width: auto; padding: 8px 20px;">Publicar</button>
            </form>
        </div>

        <h3 style="color: #ffcc00; border-bottom: 2px solid #333; padding-bottom: 8px;">Publicações Recentes</h3>
        <div style="margin-top: 15px;">
            {lista_posts_html}
        </div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Painel / Feed — JOBOSAN", content=conteudo)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        if len(nome) < 2 or "@" not in email or len(senha) < 6:
            flash("Preencha os campos corretamente (senha mínima de 6 dígitos).", "erro")
        else:
            try:
                with conectar() as conn:
                    cur = conn.execute(
                        "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
                        (nome, email, generate_password_hash(senha), agora())
                    )
                    uid = cur.lastrowid
                    conn.execute("INSERT INTO progresso (usuario_id, atualizado_em) VALUES (?, ?)", (uid, agora()))

                session.permanent = True
                session["usuario_id"] = uid
                session["usuario_nome"] = nome
                
                return redirect(url_for("painel"))
            except sqlite3.IntegrityError:
                flash("Este e-mail já está cadastrado.", "erro")

    return render_template_string(LAYOUT_GERAL, title="Criar Conta — JOBOSAN", content=REGISTRO_HTML)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
 
