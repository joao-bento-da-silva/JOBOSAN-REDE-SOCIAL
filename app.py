import os
from flask import Blueprint, render_template_string, request, redirect, url_for, session

rede_social_bp = Blueprint('rede_social', __name__)

# Importa a função de banco do arquivo principal
from __main__ import get_db

# Tenta carregar a IA do Gemini se disponível
TEM_GEMINI = False
try:
    from google import genai
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        TEM_GEMINI = True
except Exception:
    pass

# Layout específico e limpo para a rede social profissional
LAYOUT_REDE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jobosan Social</title>
    <style>
        :root { --bg-color: #030712; --card-bg: rgba(31, 41, 55, 0.6); --text-main: #f3f4f6; --text-muted: #9ca3af; --primary: #10b981; }
        body { background-color: var(--bg-color); color: var(--text-main); font-family: sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 650px; margin: 0 auto; }
        .bloco { background: var(--card-bg); padding: 20px; border-radius: 14px; margin-bottom: 20px; border: 1px solid rgba(16, 185, 129, 0.2); backdrop-filter: blur(10px); }
        textarea, input[type="text"] { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.3); color: white; box-sizing: border-box; margin-top: 5px; }
        button { background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: opacity 0.2s; }
        button:hover { opacity: 0.9; }
        .post { background: rgba(17, 24, 39, 0.7); padding: 15px; border-radius: 10px; margin-top: 15px; border: 1px solid rgba(255,255,255,0.05); }
        .header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .btn-sair { background: #ef4444; font-size: 12px; padding: 6px 12px; text-decoration: none; border-radius: 6px; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-top">
            <span>🌐 <b>Jobosan Social Profissional</b></span>
            <a href="/sair" class="btn-sair">Sair</a>
        </div>
        {{ conteudo | safe }}
    </div>
</body>
</html>
"""

@rede_social_bp.route("/plataforma", methods=["GET", "POST"])
def plataforma():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))

    conn, db_type = get_db()
    c = conn.cursor()
    ph = "%s" if db_type == "postgres" else "?"

    # Garante que as tabelas essenciais existem
    if db_type == "postgres":
        c.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER,
                conteudo TEXT,
                midia_url TEXT,
                curtidas INTEGER DEFAULT 0
            )
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                conteudo TEXT,
                midia_url TEXT,
                curtidas INTEGER DEFAULT 0
            )
        """)
    conn.commit()

    # Processa nova postagem ou interação com a IA
    if request.method == "POST":
        acao = request.form.get("acao")
        
        if acao == "postar":
            texto = request.form.get("texto")
            midia = request.form.get("midia_url", "")
            if texto:
                c.execute(f"INSERT INTO posts (usuario_id, conteudo, midia_url, curtidas) VALUES ({ph}, {ph}, {ph}, 0)", 
                          (session["usuario_id"], texto, midia))
                conn.commit()
                
        elif acao == "curtir":
            post_id = request.form.get("post_id")
            c.execute(f"UPDATE posts SET curtidas = curtidas + 1 WHERE id = {ph}", (post_id,))
            conn.commit()
            
        elif acao == "perguntar_ia" and TEM_GEMINI:
            pergunta = request.form.get("pergunta_ia")
            if pergunta:
                try:
                    resposta_ia = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"Responda de forma profissional e útil para um usuário da rede social Jobosan: {pergunta}"
                    ).text
                    session["ultima_resposta_ia"] = resposta_ia
                except Exception:
                    session["ultima_resposta_ia"] = "Desculpe, não consegui processar a resposta da IA no momento."
        
        return redirect(url_for("rede_social.plataforma"))

    # Busca postagens
    c.execute("SELECT p.*, u.nome FROM posts p JOIN usuarios u ON p.usuario_id = u.id ORDER BY p.id DESC LIMIT 20")
    posts = c.fetchall()
    
    resposta_ia_atual = session.pop("ultima_resposta_ia", None)
    conn.close()

    # Monta o HTML da interface da rede social
    conteudo = '''
    <div class="bloco">
        <h3>Criar Publicação</h3>
        <form method="POST">
            <input type="hidden" name="acao" value="postar">
            <textarea name="texto" rows="3" placeholder="O que você deseja compartilhar profissionalmente hoje?" required></textarea>
            <input type="text" name="midia_url" placeholder="Link de imagem ou vídeo (opcional) [ex: https://...]" style="margin-top: 10px;">
            <button type="submit" style="margin-top: 10px;">Publicar</time>
        </form>
    </div>
    '''

    if TEM_GEMINI:
        conteudo += f'''
        <div class="bloco" style="border-color: rgba(59, 130, 246, 0.3);">
            <h3>🤖 Assistente IA Jobosan</h3>
            <form method="POST">
                <input type="hidden" name="acao" value="perguntar_ia">
                <input type="text" name="pergunta_ia" placeholder=" Tire uma dúvida ou peça ajuda para criar um texto..." required>
                <button type="submit" style="margin-top: 10px; background: #3b82f6;">Perguntar à IA</button>
            </form>
        '''
        if resposta_ia_atual:
            conteudo += f'''<div style="background: rgba(59, 130, 246, 0.1); padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid rgba(59, 130, 246, 0.2);"><b>IA:</b> {resposta_ia_atual}</div>'''
        conteudo += '</div>'

    conteudo += '<div class="bloco"><h3>Feed de Publicações</h3>'
    if not posts:
        conteudo += '<p style="color: var(--text-muted);">Ainda não há publicações. Seja o primeiro a postar!</p>'
    else:
        for p in posts:
            conteudo += f'''
            <div class="post">
                <b>{p["nome"]}</b>
                <p style="margin: 8px 0; word-break: break-word;">{p["conteudo"]}</p>
            '''
            if p["midia_url"]:
                conteudo += f'''<div style="margin-top: 8px;"><img src="{p["midia_url"]}" style="max-width: 100%; border-radius: 8px; max-height: 300px;" onerror="this.style.display='none'"></div>'''
            
            conteudo += f'''
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 13px; color: var(--text-muted);">
                    <span>❤️ {p["curtidas"]} Curtidas</span>
                    <form method="POST" style="margin:0;">
                        <input type="hidden" name="acao" value="curtir">
                        <input type="hidden" name="post_id" value="{p["id"]}">
                        <button type="submit" style="padding: 4px 10px; font-size: 12px; background: rgba(255,255,255,0.1);">Curtir</button>
                    </form>
                </div>
            </div>
            '''
    conteudo += '</div>'

    return render_template_string(LAYOUT_REDE, conteudo=conteudo)
@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("entrar"))
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
