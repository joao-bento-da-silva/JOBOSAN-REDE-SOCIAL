from flask import Blueprint, request, session, redirect, url_for, render_template_string
from datetime import datetime
import os
import uuid
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename  

rede_social_bp = Blueprint('rede_social', __name__)

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "webm"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS

@rede_social_bp.route("/plataforma", methods=["GET", "POST"])
def plataforma():
    if "usuario_id" not in session:
        return redirect(url_for("entrar"))
    
    usuario_id = session.get("usuario_id")
    
    try:
        pagina = int(request.args.get("pagina", 1))
        if pagina < 1:
            pagina = 1
    except ValueError:
        pagina = 1

    itens_por_pagina = 20
    offset = (pagina - 1) * itens_por_pagina

    from app import get_db 
    conn, db_type = get_db()
    c = conn.cursor()

    try:
        if db_type == "postgres":
            c.execute("""
                CREATE TABLE IF NOT EXISTS postagens (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER,
                    texto TEXT,
                    arquivo TEXT,
                    data_postagem TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS curtidas (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER,
                    postagem_id INTEGER,
                    UNIQUE(usuario_id, postagem_id)
                )
            """)
        else:
            c.execute("""
                CREATE TABLE IF NOT EXISTS postagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    texto TEXT,
                    arquivo TEXT,
                    data_postagem TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS curtidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    postagem_id INTEGER
                )
            """)
        conn.commit()

        if request.method == "POST":
            texto = request.form.get("texto_post", "").strip()
            arquivo = request.files.get("arquivo")
            url_midia = None

            if arquivo and arquivo.filename and arquivo.filename.strip() != "":
                if not allowed_file(arquivo.filename):
                    return '''
                    <div style="background:#030712;color:white;min-height:100vh;padding:50px;text-align:center;font-family:sans-serif;">
                        <h2 style="color:#ef4444;">❌ Formato de ficheiro não permitido</h2>
                        <p style="margin:20px 0;">Envie imagens (PNG, JPG) ou vídeos (MP4, MOV, WEBM).</p>
                        <a href="/plataforma" style="color:#10b981;font-size:18px;">← Voltar</a>
                    </div>
                    ''', 400

                extensao = arquivo.filename.rsplit(".", 1)[1].lower()
                nome_seguro = secure_filename(arquivo.filename) or "midia"
                nome_temporario = f"jobosan_{uuid.uuid4().hex}.{extensao}"
                pasta_temp = "/tmp" if os.path.exists("/tmp") else os.path.dirname(__file__)
                caminho_temp = os.path.join(pasta_temp, nome_temporario)

                try:
                    arquivo.save(caminho_temp)
                    if not os.path.exists(caminho_temp) or os.path.getsize(caminho_temp) <= 0:
                        raise Exception("Ficheiro vazio ou não guardado")

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
                except Exception as e:
                    return f'''
                    <div style="background:#030712;color:white;min-height:100vh;padding:50px;text-align:center;font-family:sans-serif;">
                        <h2 style="color:#ef4444;">❌ Erro ao enviar mídia</h2>
                        <p style="color:#cbd5e1;margin:20px 0;">{str(e)}</p>
                        <a href="/plataforma" style="color:#10b981;font-size:18px;">← Voltar</a>
                    </div>
                    ''', 500
                finally:
                    if os.path.exists(caminho_temp):
                        try: os.remove(caminho_temp)
                        except Exception: pass

            if texto or url_midia:
                ph = "%s" if db_type == "postgres" else "?"
                c.execute(
                    f"INSERT INTO postagens (usuario_id, texto, arquivo, data_postagem) VALUES ({ph}, {ph}, {ph}, {ph})",
                    (usuario_id, texto, url_midia, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
            return redirect(url_for("rede_social.plataforma"))

        if "curtir" in request.args:
            pid = request.args.get("curtir")
            try:
                ph = "%s" if db_type == "postgres" else "?"
                c.execute(f"INSERT INTO curtidas (usuario_id, postagem_id) VALUES ({ph}, {ph})", (usuario_id, pid))
            except Exception:
                ph = "%s" if db_type == "postgres" else "?"
                c.execute(f"DELETE FROM curtidas WHERE usuario_id = {ph} AND postagem_id = {ph}", (usuario_id, pid))
            conn.commit()
            return redirect(url_for("rede_social.plataforma", pagina=pagina) + "#post-" + str(pid))
        
        ph = "%s" if db_type == "postgres" else "?"
        c.execute(f"SELECT nome FROM usuarios WHERE id = {ph}", (usuario_id,))
        usuario_dados = c.fetchone()
        nome_usuario = usuario_dados["nome"] if usuario_dados else "Utilizador"
        
        c.execute("SELECT COUNT(*) FROM postagens")
        total_posts = c.fetchone()[0]
        total_paginas = (total_posts + itens_por_pagina - 1) // itens_por_pagina or 1

        query_posts = f"""
            SELECT p.id, p.texto, p.arquivo, p.data_postagem, u.nome,
            (SELECT COUNT(*) FROM curtidas c WHERE c.postagem_id = p.id) as total_curtidas,
            EXISTS(SELECT 1 FROM curtidas c WHERE c.postagem_id = p.id AND c.usuario_id = {ph}) as curtiu
            FROM postagens p JOIN usuarios u ON p.usuario_id = u.id 
            ORDER BY p.data_postagem DESC LIMIT {ph} OFFSET {ph}
        """
        c.execute(query_posts, (usuario_id, itens_por_pagina, offset))
        postagens = c.fetchall()

    finally:
        conn.close()
    
    posts_html = ""
    for p in postagens:
        pid, texto, arquivo_url, data, autor, curtidas, curtiu = p
        
        posts_html += f'''<div id="post-{pid}" style="background:rgba(31,41,55,0.5); padding:18px; border-radius:14px; margin-bottom:15px; border:1px solid rgba(16,185,129,0.2);">
            <h4 style="color:#10b981; font-size:15px; font-weight:bold;">{autor}</h4>
            <p style="font-size:11px; color:#9ca3af; margin-bottom:10px;">{data}</p>
            {f'<p style="font-size:14px; line-height:1.5; color:#f3f4f6;">{texto}</p>' if texto else ''}'''
        
        if arquivo_url:
            if any(ext in arquivo_url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif"]) or "/image/upload/" in arquivo_url.lower():
                posts_html += f'<img src="{arquivo_url}" style="max-width:100%; border-radius:10px; margin-top:10px;">'
            else:
                posts_html += f'<video controls style="max-width:100%; border-radius:10px; margin-top:10px;"><source src="{arquivo_url}"></video>'

        posts_html += f'''<div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.1);">
            <a href="/plataforma?curtir={pid}&pagina={pagina}#post-{pid}" style="font-size:12px; text-decoration:none; padding:6px 14px; background:rgba(16,185,129,0.15); color:#34d399; border-radius:8px; display:inline-block; font-weight:600;">👍 {curtidas} Curtida(s)</a>
        </div></div>'''
    
    if not posts_html:
        posts_html = '<p style="text-align:center; color:#9ca3af; padding:30px;">Ainda não há publicações. Seja o primeiro a partilhar algo!</p>'

    from app import LAYOUT
    conteudo = f'''
    <div class="bloco">
        <h2>🌐 Rede Social Jobosan</h2>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:20px;">Partilhe ideias, imagens ou vídeos com a comunidade.</p>
        
        <form method="POST" enctype="multipart/form-data">
            <textarea name="texto_post" rows="3" placeholder="Em que está a pensar, {nome_usuario}?"></textarea>
            <div style="margin: 12px 0;">
                <label style="font-size:12px; color:var(--text-muted); display:block; margin-bottom:5px;">Anexar Imagem ou Vídeo:</label>
                <input type="file" name="arquivo" accept="image/*,video/*">
            </div>
            <button type="submit">Publicar</button>
        </form>
    </div>

    <div class="bloco">
        <h3>Feed Recente</h3>
        <div style="margin-top:15px;">{posts_html}</div>
    </div>
    '''
    
    return render_template_string(LAYOUT, conteudo=conteudo)
