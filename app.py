import os
import sqlite3
import random
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, send_from_directory

# -------------------------------------------------------------------
# CONFIGURAÇÕES E CONSTANTES GLOBAIS
# -------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov', 'avi'}

NOME_APLICACAO = "Rede Jobosan"
EMAIL_DONO = "dono@jobosan.com"
SENHA_MESTRA_ACESSO = "1234"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_jobosan_rede_social")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Limite de 50MB para uploads

# Suporte ao PostgreSQL para hospedagem no Render
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

DATABASE_URL = os.getenv("DATABASE_URL")

# -------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def usuario_logado():
    return 'usuario_id' in session

def eh_dono():
    return session.get('usuario_email', '').strip().lower() == EMAIL_DONO.lower()

def responder_ia(pergunta):
    pergunta_clean = pergunta.lower().strip()
    conn, db_type = get_db()
    c = conn.cursor()
    param = "%s" if db_type == "postgres" else "?"
    c.execute(f"SELECT resposta_customizada FROM regras_ia WHERE pergunta_chave = {param}", (pergunta_clean,))
    res = c.fetchone()
    conn.close()
    if res:
        return res['resposta_customizada'] if isinstance(res, dict) or hasattr(res, 'keys') else res[0]
    return f"Não encontrei uma resposta específica para '{pergunta}', mas continuo aprendendo!"

# -------------------------------------------------------------------
# BANCO DE DADOS
# -------------------------------------------------------------------
def get_db():
    if DATABASE_URL and POSTGRES_AVAILABLE:
        try:
            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.DictCursor)
            return conn, "postgres"
        except Exception as e:
            print(f"Erro ao conectar ao PostgreSQL: {e}")

    db_path = os.path.join(BASE_DIR, "jobosan_rede_social.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"

def init_db():
    conn, db_type = get_db()
    c = conn.cursor()
    
    if db_type == "postgres":
        c.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                pontos INTEGER DEFAULT 0,
                pontos_bentinho INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS postagens (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER,
                texto TEXT,
                arquivo TEXT,
                data_postagem TEXT
            );
            CREATE TABLE IF NOT EXISTS curtidas (
                usuario_id INTEGER,
                postagem_id INTEGER,
                PRIMARY KEY (usuario_id, postagem_id)
            );
            CREATE TABLE IF NOT EXISTS conversas_ia (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER,
                pergunta TEXT,
                resposta TEXT,
                data_hora TEXT
            );
            CREATE TABLE IF NOT EXISTS regras_ia (
                pergunta_chave TEXT PRIMARY KEY,
                resposta_customizada TEXT
            );
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                pontos INTEGER DEFAULT 0,
                pontos_bentinho INTEGER DEFAULT 0
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS postagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                texto TEXT,
                arquivo TEXT,
                data_postagem TEXT
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS curtidas (
                usuario_id INTEGER,
                postagem_id INTEGER,
                PRIMARY KEY (usuario_id, postagem_id)
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversas_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                pergunta TEXT,
                resposta TEXT,
                data_hora TEXT
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS regras_ia (
                pergunta_chave TEXT PRIMARY KEY,
                resposta_customizada TEXT
            );
        """)
    
    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------------------
# ROTA PARA SERVIR MÍDIAS ENVIADAS
# -------------------------------------------------------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------------------------------------------------------
# ROTAS PRINCIPAIS, LOGIN E CADASTRO
# -------------------------------------------------------------------
@app.route('/')
def index():
    if usuario_logado():
        return redirect(url_for('plataforma'))
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        conn, db_type = get_db()
        c = conn.cursor()
        param = "%s" if db_type == "postgres" else "?"
        
        c.execute(f"SELECT * FROM usuarios WHERE email = {param}", (email,))
        if c.fetchone():
            conn.close()
            flash("E-mail já cadastrado!", "danger")
            return redirect(url_for('cadastro'))
            
        c.execute(
            f"INSERT INTO usuarios (nome, email, senha, pontos, pontos_bentinho) VALUES ({param}, {param}, {param}, 0, 0)",
            (nome, email, senha)
        )
        conn.commit()
        conn.close()
        
        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for('login'))
        
    return render_template_string('''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cadastro — {{ nome_app }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen flex items-center justify-center p-4">
    <div class="bg-gray-800 p-8 rounded-2xl border border-yellow-500/40 max-w-md w-full shadow-2xl">
        <div class="text-center mb-6">
            <h1 class="text-4xl font-black text-yellow-500 tracking-wider mb-1">JOBOSAN</h1>
            <p class="text-xs uppercase tracking-widest text-gray-400 font-bold">Rede Social & Plataforma</p>
        </div>
        
        <h2 class="text-xl font-bold text-gray-200 text-center mb-6 border-b border-gray-700 pb-3">📝 Criar Nova Conta</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="mb-4 p-3 rounded-lg text-sm font-bold text-center {% if category == 'danger' %}bg-red-900/50 text-red-400 border border-red-700{% else %}bg-green-900/50 text-green-400 border border-green-700{% endif %}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm text-gray-300 font-medium mb-1">Nome Completo</label>
                <input type="text" name="nome" required placeholder="Seu nome" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:border-yellow-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm text-gray-300 font-medium mb-1">E-mail</label>
                <input type="email" name="email" required placeholder="seuemail@exemplo.com" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:border-yellow-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm text-gray-300 font-medium mb-1">Senha</label>
                <input type="password" name="senha" required placeholder="••••••••" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:border-yellow-500 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-extrabold py-3 rounded-lg transition shadow-lg text-base">Cadastrar na Jobosan</button>
        </form>
        <p class="text-center text-sm text-gray-400 mt-6">Já tem uma conta? <a href="/login" class="text-yellow-500 hover:underline font-bold">Faça login</a></p>
    </div>
</body>
</html>''', nome_app=NOME_APLICACAO)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        conn, db_type = get_db()
        c = conn.cursor()
        param = "%s" if db_type == "postgres" else "?"
        
        c.execute(f"SELECT * FROM usuarios WHERE email = {param} AND senha = {param}", (email, senha))
        usuario = c.fetchone()
        conn.close()
        
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_email'] = usuario['email']
            return redirect(url_for('plataforma'))
        else:
            flash("E-mail ou senha incorretos.", "danger")
            return redirect(url_for('login'))
            
    return render_template_string('''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — {{ nome_app }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen flex items-center justify-center p-4">
    <div class="bg-gray-800 p-8 rounded-2xl border border-yellow-500/40 max-w-md w-full shadow-2xl">
        <div class="text-center mb-6">
            <h1 class="text-4xl font-black text-yellow-500 tracking-wider mb-1">JOBOSAN</h1>
            <p class="text-xs uppercase tracking-widest text-gray-400 font-bold">Rede Social & Plataforma</p>
        </div>

        <h2 class="text-xl font-bold text-gray-200 text-center mb-6 border-b border-gray-700 pb-3">🔑 Entrar na Plataforma</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="mb-4 p-3 rounded-lg text-sm font-bold text-center {% if category == 'danger' %}bg-red-900/50 text-red-400 border border-red-700{% else %}bg-green-900/50 text-green-400 border border-green-700{% endif %}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm text-gray-300 font-medium mb-1">E-mail</label>
                <input type="email" name="email" required placeholder="seuemail@exemplo.com" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:border-yellow-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm text-gray-300 font-medium mb-1">Senha</label>
                <input type="password" name="senha" required placeholder="••••••••" class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:border-yellow-500 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-extrabold py-3 rounded-lg transition shadow-lg text-base">Entrar na Jobosan</button>
        </form>
        <p class="text-center text-sm text-gray-400 mt-6">Não tem uma conta? <a href="/cadastro" class="text-yellow-500 hover:underline font-bold">Cadastre-se</a></p>
    </div>
</body>
</html>''', nome_app=NOME_APLICACAO)


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))

# -------------------------------------------------------------------
# PLATAFORMA FEED E INTERAÇÕES (COM FOTOS E VÍDEOS)
# -------------------------------------------------------------------
@app.route("/plataforma", methods=["GET", "POST"])
def plataforma():
    if not usuario_logado():
        return redirect(url_for("login"))
    usuario_id = session["usuario_id"]
    
    try:
        pagina = int(request.args.get("pagina", 1))
        if pagina < 1: pagina = 1
    except ValueError:
        pagina = 1

    itens_por_pagina = 20
    offset = (pagina - 1) * itens_por_pagina

    # Criar Postagem (Texto + Mídia)
    if request.method == "POST":
        texto = request.form.get("texto_post", "").strip()
        file = request.files.get("midia_post")
        nome_arquivo_salvo = None

        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            nome_arquivo_salvo = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo_salvo))

        if texto or nome_arquivo_salvo:
            conn, db_type = get_db()
            try:
                c = conn.cursor()
                param = "%s" if db_type == "postgres" else "?"
                c.execute(
                    f"INSERT INTO postagens (usuario_id, texto, arquivo, data_postagem) VALUES ({param}, {param}, {param}, {param})",
                    (usuario_id, texto, nome_arquivo_salvo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
            finally:
                conn.close()
            return redirect(url_for("plataforma"))

    # Curtidas
    if "curtir" in request.args:
        pid = request.args.get("curtir")
        conn, db_type = get_db()
        c = conn.cursor()
        param = "%s" if db_type == "postgres" else "?"
        try:
            c.execute(f"INSERT INTO curtidas (usuario_id, postagem_id) VALUES ({param}, {param})", (usuario_id, pid))
        except (sqlite3.IntegrityError, Exception):
            c.execute(f"DELETE FROM curtidas WHERE usuario_id = {param} AND postagem_id = {param}", (usuario_id, pid))
        conn.commit()
        conn.close()
        return redirect(url_for("plataforma", pagina=pagina) + "#post-" + str(pid))
    
    # Dados do usuário
    conn, db_type = get_db()
    c = conn.cursor()
    param = "%s" if db_type == "postgres" else "?"
    c.execute(f"SELECT nome, pontos, email FROM usuarios WHERE id = {param}", (usuario_id,))
    usuario_dados = c.fetchone()
    if not usuario_dados:
        conn.close()
        session.clear()
        return redirect(url_for("login"))
        
    nome_usuario = usuario_dados['nome']
    total_pontos = usuario_dados['pontos']
    email_usuario = usuario_dados['email']
    
    # Paginação
    c.execute("SELECT COUNT(*) FROM postagens")
    total_posts_banco = c.fetchone()[0]
    total_paginas = (total_posts_banco + itens_por_pagina - 1) // itens_por_pagina or 1

    # Buscar Postagens
    query = f"""
        SELECT p.id, p.texto, p.arquivo, p.data_postagem, u.nome,
        (SELECT COUNT(*) FROM curtidas c WHERE c.postagem_id = p.id) as total_curtidas,
        EXISTS(SELECT 1 FROM curtidas c WHERE c.postagem_id = p.id AND c.usuario_id = {param}) as curtiu
        FROM postagens p JOIN usuarios u ON p.usuario_id = u.id 
        ORDER BY p.data_postagem DESC LIMIT {param} OFFSET {param}
    """
    c.execute(query, (usuario_id, itens_por_pagina, offset))
    postagens = c.fetchall()
    conn.close()
    
    posts_html = ""
    for p in postagens:
        pid, texto, arquivo, data, autor, curtidas, curtiu = p['id'], p['texto'], p['arquivo'], p['data_postagem'], p['nome'], p['total_curtidas'], p['curtiu']
        
        midia_html = ""
        if arquivo:
            ext = arquivo.rsplit('.', 1)[1].lower() if '.' in arquivo else ''
            url_midia = url_for('uploaded_file', filename=arquivo)
            if ext in ['mp4', 'webm', 'mov', 'avi']:
                midia_html = f'''<div class="mt-3 overflow-hidden rounded-lg bg-black flex justify-center">
                    <video controls class="max-h-96 w-full object-contain"><source src="{url_midia}">Seu navegador não suporta vídeos.</video>
                </div>'''
            elif ext in ['png', 'jpg', 'jpeg', 'gif']:
                midia_html = f'''<div class="mt-3 overflow-hidden rounded-lg bg-black flex justify-center">
                    <img src="{url_midia}" alt="Mídia da postagem" class="max-h-96 w-full object-contain">
                </div>'''

        posts_html += f'''<div id="post-{pid}" class="bg-gray-800 p-4 rounded-lg border border-yellow-500/30 mb-4">
            <h4 class="font-bold text-yellow-400">{autor}</h4><p class="text-sm text-gray-400">{data}</p>
            {f'<p class="my-3 whitespace-pre-wrap">{texto}</p>' if texto else ''}
            {midia_html}
            <div class="mt-3 pt-3 border-t border-gray-700">
                <a href="/plataforma?curtir={pid}&pagina={pagina}#post-{pid}" class="text-{'red' if curtiu else 'gray'}-400 font-bold">👍 {curtidas} Curtida{'s' if curtidas != 1 else ''}</a>
            </div>
        </div>'''
    
    if not posts_html:
        posts_html = '<p class="text-center text-gray-500 py-10">Ainda não há postagens. Seja o primeiro a publicar!</p>'
    
    btn_anterior = f'<a href="/plataforma?pagina={pagina - 1}" class="bg-gray-700 hover:bg-gray-600 text-yellow-400 font-bold px-4 py-2 rounded-lg">← Anterior</a>' if pagina > 1 else '<span class="text-gray-600 bg-gray-800 px-4 py-2 rounded-lg cursor-not-allowed">← Anterior</span>'
    btn_proxima = f'<a href="/plataforma?pagina={pagina + 1}" class="bg-gray-700 hover:bg-gray-600 text-yellow-400 font-bold px-4 py-2 rounded-lg">Próxima →</a>' if pagina < total_paginas else '<span class="text-gray-600 bg-gray-800 px-4 py-2 rounded-lg cursor-not-allowed">Próxima →</span>'

    paginacao_html = f'''<div class="flex justify-between items-center bg-gray-800 p-4 rounded-lg border border-yellow-500/30 my-6">
        {btn_anterior}
        <span class="text-gray-300 font-bold text-sm">Página {pagina} de {total_paginas}</span>
        {btn_proxima}
    </div>'''

    botao_admin = f'<a href="/area_privada" class="bg-red-600 text-white px-4 py-2 rounded-lg text-sm ml-2 font-bold">🔒 Área Privada</a>' if email_usuario.strip().lower() == EMAIL_DONO.lower() else ""
    
    return render_template_string(f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Plataforma — {NOME_APLICACAO}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>.tab-content{{display:block;}}.tab-content.hidden{{display:none !important;}}</style>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-6 max-w-4xl">
        <div class="flex flex-wrap justify-between items-center border-b border-gray-700 pb-4 mb-6">
            <div><h1 class="text-2xl font-bold text-yellow-500">⚡ {NOME_APLICACAO}</h1><p class="text-gray-400">Bem-vindo, {nome_usuario}!</p></div>
            <div class="text-right">
                <p class="text-sm text-gray-400">Pontos</p><p class="text-xl font-bold text-yellow-500">{total_pontos}</p>
                <a href="/sair" class="text-red-400 text-sm ml-2">Sair</a> {botao_admin}
            </div>
        </div>
        <div class="flex flex-wrap gap-2 mb-6 border-b border-gray-700 pb-2">
            <button class="tab-btn bg-yellow-600 text-black px-4 py-2 rounded-t-lg font-bold" onclick="switchTab('rede', event)">Rede Social</button>
            <button class="tab-btn bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-t-lg" onclick="switchTab('jogos', event)">🎮 Jogos</button>
            <button class="tab-btn bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-t-lg" onclick="switchTab('ia', event)">🤖 IA</button>
        </div>

        <div id="tab-rede" class="tab-content">
            <form method="POST" enctype="multipart/form-data" class="bg-gray-800 p-5 rounded-lg border border-yellow-500/30 mb-6">
                <h3 class="text-yellow-500 font-bold mb-3">✍️ Nova Postagem</h3>
                <textarea name="texto_post" rows="3" placeholder="Escreva algo..." class="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white mb-3"></textarea>
                <div class="mb-3">
                    <label class="block text-sm text-gray-400 mb-1">Anexar Foto ou Vídeo:</label>
                    <input type="file" name="midia_post" accept="image/*,video/*" class="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-yellow-600 file:text-black hover:file:bg-yellow-500 cursor-pointer">
                </div>
                <button type="submit" class="bg-yellow-600 text-black font-bold py-2 px-6 rounded-lg">📤 Publicar</button>
            </form>
            <h3 class="text-yellow-500 font-bold mb-3">📰 Postagens</h3>
            {posts_html}
            {paginacao_html}
        </div>

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
    </div>

    <script>
        function switchTab(nome, evt) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => {{
                b.classList.remove('bg-yellow-600', 'text-black');
                b.classList.add('bg-gray-700');
            }});
            document.getElementById('tab-' + nome).classList.remove('hidden');
            evt.target.classList.remove('bg-gray-700');
            evt.target.classList.add('bg-yellow-600', 'text-black');
        }}
    </script>
</body>
</html>''')

# -------------------------------------------------------------------
# ÁREA PRIVADA & PAINEL DO DONO
# -------------------------------------------------------------------
@app.route("/area_privada", methods=["GET", "POST"])
def area_privada():
    if not usuario_logado() or not eh_dono():
        return '''<div style="text-align:center;padding:50px;background:#0f172a;color:white;font-family:sans-serif;">
            <h2 style="color:red;">🚫 ACESSO NEGADO — Área exclusiva do dono</h2>
            <br><a href="/plataforma" style="color:#f59e0b;">Voltar</a>
        </div>'''
    if request.method == "POST":
        if request.form.get("senha_mestra") == SENHA_MESTRA_ACESSO:
            return redirect(url_for("painel_dono"))
        return '''<div style="text-align:center;padding:50px;background:#0f172a;color:white;font-family:sans-serif;">
            <h2 style="color:red;">❌ Senha incorreta!</h2>
            <br><a href="/area_privada" style="color:#f59e0b;">Tentar novamente</a>
        </div>'''
    return render_template_string('''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>🔒 Área Privada</title>
    <style>body{background:linear-gradient(180deg,#0f172a,#1e293b);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:Arial,sans-serif;}
    .caixa{background:rgba(15,23,42,0.9);padding:40px;border-radius:12px;border:2px solid #f59e0b;max-width:400px;width:90%;text-align:center;}
    input{width:100%;padding:12px;margin:8px 0;background:#020617;border:1px solid #334155;color:white;border-radius:6px;box-sizing:border-box;}
    button{width:100%;padding:12px;background:#f59e0b;color:black;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}
    a{color:#f59e0b;text-decoration:none;display:block;margin-top:20px;}</style>
</head>
<body>
    <div class="caixa">
        <h1 style="color:#f59e0b;">🔒 ÁREA PRIVADA</h1>
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
        return redirect(url_for("login"))
    conn, _ = get_db()
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
    <title>⚙️ Painel do Dono</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-200 p-6 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-yellow-500 mb-6">⚙️ PAINEL DO DONO</h1>
    <a href="/plataforma" class="text-yellow-500 mb-4 inline-block font-bold">← Voltar</a>
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

# -------------------------------------------------------------------
# IA E JOGOS
# -------------------------------------------------------------------
@app.route("/responder_ia", methods=["POST"])
def responder_ia_rota():
    if not usuario_logado():
        return "Não autorizado", 401
    pergunta = request.form.get("pergunta", "").strip()
    if not pergunta:
        return "Digite uma pergunta!"
    resposta = responder_ia(pergunta)
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn, db_type = get_db()
    c = conn.cursor()
    param = "%s" if db_type == "postgres" else "?"
    c.execute(f"INSERT INTO conversas_ia (usuario_id, pergunta, resposta, data_hora) VALUES ({param}, {param}, {param}, {param})",
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
            conn, db_type = get_db()
            c = conn.cursor()
            
            if db_type == "postgres":
                c.execute("INSERT INTO regras_ia (pergunta_chave, resposta_customizada) VALUES (%s, %s) ON CONFLICT (pergunta_chave) DO UPDATE SET resposta_customizada = EXCLUDED.resposta_customizada", (pergunta_chave, resposta_customizada))
            else:
                c.execute("INSERT OR REPLACE INTO regras_ia (pergunta_chave, resposta_customizada) VALUES (?, ?)", (pergunta_chave, resposta_customizada))
                
            conn.commit()
            conn.close()
            return "✅ IA ensinada com sucesso!"
        except Exception as e:
            return f"❌ Erro ao ensinar IA: {str(e)}"
    return "Preencha todos os campos!", 400

@app.route("/jogo_cartas", methods=["GET", "POST"])
def jogo_cartas():
    if not usuario_logado():
        return redirect(url_for("login"))
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
                        conn, db_type = get_db()
                        c = conn.cursor()
                        param = "%s" if db_type == "postgres" else "?"
                        c.execute(f"UPDATE usuarios SET pontos = pontos + {param} WHERE id = {param}", (valor, session["usuario_id"]))
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
    <title>🃏 Jogo das Cartas</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-6 max-w-2xl mx-auto bg-gray-900 text-gray-200">
    <a href="/plataforma" class="text-yellow-500 font-bold">← Voltar</a>
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

@app.route("/jogo_bentinho", methods=["GET", "POST"])
def jogo_bentinho():
    if not usuario_logado():
        return redirect(url_for("login"))
    
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
                conn, db_type = get_db()
                c = conn.cursor()
                param = "%s" if db_type == "postgres" else "?"
                c.execute(f"UPDATE usuarios SET pontos_bentinho = pontos_bentinho + {param} WHERE id = {param}", (pts, session["usuario_id"]))
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
    <title>🎮 Segredo dos Números</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="flex items-center justify-center p-4 bg-gray-900 text-gray-200 min-h-screen">
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
                <button type="submit" name="acao" value="reiniciar" class="bg-gray-600 text-white px-6 py-3 rounded-lg font-bold">🔄 Reiniciar</button>
            </div>
        </form>
        <p class="text-center mt-6"><a href="/plataforma" class="text-yellow-500 font-bold">← Voltar</a></p>
    </div>
</body>
</html>''')

# -------------------------------------------------------------------
# EXECUÇÃO DO APP
# -------------------------------------------------------------------
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)
