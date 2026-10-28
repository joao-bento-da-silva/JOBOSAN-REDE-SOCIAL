from flask import Flask, render_template, redirect, url_for, session, request
import os
import psycopg2
import psycopg2.extras
sqlite3 = None
try:
    import sqlite3
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave_secreta_padrao")

# Layout base para manter todo o design e aspeto visual intactos
LAYOUT = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jobosan</title>
    <style>
        :root { --bg-color: #030712; --card-bg: rgba(31, 41, 55, 0.5); --text-main: #f3f4f6; --text-muted: #9ca3af; --primary: #10b981; }
        body { background-color: var(--bg-color); color: var(--text-main); font-family: sans-serif; margin: 0; padding: 20px; }
        .bloco { background: var(--card-bg); padding: 20px; border-radius: 14px; margin-bottom: 20px; border: 1px solid rgba(16, 185, 129, 0.2); }
        textarea, input[type="text"], input[type="password"] { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; margin-top: 5px; }
        button { background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div style="max-width: 700px; margin: 0 auto;">
        {{ conteudo | safe }}
    </div>
</body>
</html>
"""

def get_db():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.DictCursor)
        return conn, "postgres"
    else:
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

# Registo do Blueprint da rede social
from rede_social import rede_social_bp
app.register_blueprint(rede_social_bp)

@app.route("/")
def index():
    if "usuario_id" in session:
        return redirect(url_for("rede_social.plataforma"))
    return redirect(url_for("entrar"))

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    # Página de login/entrada existente no seu projeto
    if request.method == "POST":
        # Lógica de login...
        pass
    
    conteudo = '''
    <div class="bloco">
        <h2>Entrar no Jobosan</h2>
        <form method="POST">
            <label>Utilizador:</label>
            <input type="text" name="nome" required>
            <button type="submit" style="margin-top: 15px;">Entrar</button>
        </form>
    </div>
    '''
    return render_template_string(LAYOUT, conteudo=conteudo)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
