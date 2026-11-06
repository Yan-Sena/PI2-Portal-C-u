"""Portal CEU Aricanduva - API Flask + SQLite (protótipo acadêmico, UNIVESP)."""
import hmac
import os
import re
import sqlite3

from flask import Flask, g, jsonify, request

BASE = os.path.dirname(os.path.abspath(__file__))
SEED_AVISOS = [
    ("EMEI CEU Aricanduva", "Reunião de pais e responsáveis",
     "Haverá reunião pedagógica sobre o semestre em 12/11/2026, às 18h."),
    ("CEI Dirce Migliaccio", "Atualização da carteira de vacinação",
     "Entregue a cópia atualizada na secretaria da unidade até 20/11/2026."),
    ("EMEI Dom José Gaspar", "Festa de encerramento do ano",
     "Famílias convidadas em 05/12/2026. Cada família pode levar um prato para compartilhar."),
]
SEED_EVENTOS = [
    ("Circuito Spcine", "Sessão de cinema gratuita", "14/11/2026, 16h. Entrada gratuita, com ingressos retirados no local."),
    ("Teatro", "Espetáculo infantil", "21/11/2026, 15h. Indicado para toda a família."),
    ("Biblioteca Mário Quintana", "Hora do conto", "Todos os sábados, às 10h, para crianças e acompanhantes."),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS avisos (
  id INTEGER PRIMARY KEY AUTOINCREMENT, unidade TEXT NOT NULL,
  titulo TEXT NOT NULL, texto TEXT NOT NULL, criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS eventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT NOT NULL,
  titulo TEXT NOT NULL, texto TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS municipes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
  cpf TEXT NOT NULL UNIQUE, consentimento INTEGER NOT NULL,
  criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def cpf_valido(valor):
    c = re.sub(r"\D", "", valor or "")
    if len(c) != 11 or c == c[0] * 11:
        return False
    for t in (9, 10):
        soma = sum(int(c[i]) * (t + 1 - i) for i in range(t))
        if ((soma * 10) % 11) % 10 != int(c[t]):
            return False
    return True


def create_app(db_path=None):
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", os.path.join(BASE, "portal.db"))
    app.config["ADMIN_TOKEN"] = os.environ.get("ADMIN_TOKEN", "troque-este-token")

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def fechar(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    with app.app_context():
        conn = db()
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM avisos").fetchone()[0] == 0:
            conn.executemany("INSERT INTO avisos (unidade, titulo, texto) VALUES (?,?,?)", SEED_AVISOS)
            conn.executemany("INSERT INTO eventos (categoria, titulo, texto) VALUES (?,?,?)", SEED_EVENTOS)
            conn.commit()

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/saude")
    def saude():
        return jsonify(status="ok")

    @app.get("/api/avisos")
    def listar_avisos():
        rows = db().execute("SELECT id, unidade, titulo, texto FROM avisos ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/eventos")
    def listar_eventos():
        rows = db().execute("SELECT id, categoria, titulo, texto FROM eventos ORDER BY id").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/avisos")
    def criar_aviso():
        token = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(token, app.config["ADMIN_TOKEN"]):
            return jsonify(erro="Não autorizado."), 401
        d = request.get_json(silent=True) or {}
        campos = [str(d.get(k, "")).strip() for k in ("unidade", "titulo", "texto")]
        if not all(campos):
            return jsonify(erro="Informe unidade, título e texto."), 400
        conn = db()
        cur = conn.execute("INSERT INTO avisos (unidade, titulo, texto) VALUES (?,?,?)", campos)
        conn.commit()
        return jsonify(id=cur.lastrowid, unidade=campos[0], titulo=campos[1], texto=campos[2]), 201

    @app.post("/api/municipes")
    def cadastrar():
        d = request.get_json(silent=True) or {}
        nome = str(d.get("nome", "")).strip()
        cpf = re.sub(r"\D", "", str(d.get("cpf", "")))
        erros = {}
        if len(nome.split()) < 2:
            erros["nome"] = "Informe o nome e o sobrenome."
        if not cpf_valido(cpf):
            erros["cpf"] = "Informe um CPF válido."
        if d.get("consentimento") is not True:
            erros["consentimento"] = "É necessário autorizar o uso dos dados."
        if erros:
            return jsonify(erros=erros), 400
        conn = db()
        try:
            cur = conn.execute("INSERT INTO municipes (nome, cpf, consentimento) VALUES (?,?,1)", (nome, cpf))
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify(erros={"cpf": "Este CPF já está cadastrado."}), 409
        return jsonify(id=cur.lastrowid, nome=nome), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
