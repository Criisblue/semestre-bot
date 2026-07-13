import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "datos.db"


def conectar():
    return sqlite3.connect(DB)


def init_db():
    """Crea las tablas si no existen."""
    con = conectar()
    con.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            chat_id   INTEGER PRIMARY KEY,
            semestre  TEXT,
            paralelo  TEXT
        )
    """)
    con.commit()
    con.close()

def guardar_usuario(chat_id, semestre, paralelo):
    con = conectar()
    con.execute(
        "INSERT OR REPLACE INTO usuarios (chat_id, semestre, paralelo) VALUES (?, ?, ?)",
        (chat_id, semestre, paralelo),
    )
    con.commit()
    con.close()


def obtener_usuario(chat_id):
    con = conectar()
    fila = con.execute(
        "SELECT semestre, paralelo FROM usuarios WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    con.close()
    if fila is None:
        return None
    return {"semestre": fila[0], "paralelo": fila[1]}

if __name__ == "__main__":
    init_db()
    print("Base de datos lista:", DB)