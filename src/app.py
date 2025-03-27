import os
import re
import sqlite3

import pandas as pd
from flask import Flask, flash, g, render_template, request
from flask_htmx import HTMX

DATABASE = "db/database.sqlite3"
ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}

app = Flask("openprize")
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1000 * 1000  # 32 MB
htmx = HTMX(app)


@app.route("/")
def index():
    partial_template = "index.p.html"
    init_db()
    if htmx:
        return render_template(partial_template)
    return render_template("base.html", partial_template=partial_template)


@app.route("/draw")
def draw():
    partial_template = "draw.p.html"
    ctx = {}
    conn = connect_db()
    cursor = conn.cursor()
    ctx["names_in_db"] = table_exists(conn, "names")
    prizes = cursor.execute("SELECT * FROM prizes").fetchall()
    ctx["prizes"] = prizes if prizes else None
    ctx["winners"] = fetch_winners(conn)
    if htmx:
        return render_template(partial_template, ctx=ctx)
    return render_template("base.html", partial_template=partial_template, ctx=ctx)


@app.route("/draw_name", methods=["GET", "POST"])
def draw_name():
    name = None
    prize = None
    ctx = {}
    conn = connect_db()
    ctx["names_in_db"] = table_exists(conn, "names")
    cursor = conn.cursor()

    if request.method == "POST":
        # Get the prize
        prize = request.form.get("prize", None)
        if prize == "":
            prize = None
        if prize is not None:
            prize = cursor.execute(
                "SELECT * FROM prizes WHERE id = ?", (prize,)
            ).fetchone()
        # Make sure we have names in the database
        no_names = len(cursor.execute("SELECT * FROM names").fetchall()) == 0
        if no_names:
            flash("No Names Found. Did you forget to import? ", "danger")
        else:
            name = cursor.execute(
                "SELECT * FROM names ORDER BY RANDOM() LIMIT 1"
            ).fetchone()

    prizes = cursor.execute("SELECT * FROM prizes").fetchall()
    ctx["name"] = name if name else None
    ctx["prizes"] = prizes if prizes else None
    ctx["winners"] = fetch_winners(conn)
    if htmx:
        return render_template("winner-detail.p.html", ctx=ctx)
    return render_template("base.html", partial_template="draw.p.html", ctx=ctx)


@app.route("/award_prize", methods=["POST"])
def award_prize():
    partial_template = "draw.p.html"
    ctx = {}
    conn = connect_db()
    ctx["names_in_db"] = table_exists(conn, "names")
    cursor = conn.cursor()
    name = cursor.execute(
        "SELECT * FROM names WHERE id = ?", (request.form.get("name_id"),)
    ).fetchone()
    prize = cursor.execute(
        "SELECT * FROM prizes WHERE id = ?", (request.form.get("prize_id"),)
    ).fetchone()
    log_winner(conn, name, prize)
    remove_entry(conn, name, prize)

    prizes = cursor.execute("SELECT * FROM prizes").fetchall()
    ctx["name"] = name if name else None
    ctx["prizes"] = prizes if prizes else None
    ctx["winners"] = fetch_winners(conn)
    return render_template(partial_template, ctx=ctx)


@app.route("/import_file", methods=["POST"])
def import_file():
    partial_template = "settings.p.html"
    conn = connect_db()
    setting_state = dict(fetch_settings(conn))
    file = (
        request.files["prizes"]
        if "prizes" in request.files
        else request.files["names"] if "names" in request.files else None
    )
    if file is None:
        flash("No file selected", "danger")
        return render_template(partial_template, settings=setting_state)
    if file.filename.rsplit(".", 1)[1].lower() == "csv":
        xl = pd.read_csv(file)
    else:
        xl = pd.read_excel(file)
    if file and allowed_file(file.filename):
        data_type = str(file.name)
        total_rows = import_data(conn, xl, data_type)
        flash(
            f"File uploaded successfully, {total_rows} {data_type} imported.", "success"
        )
    if htmx:
        return render_template(partial_template, settings=setting_state)
    return render_template(
        "base.html", partial_template=partial_template, settings=setting_state
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    partial_template = "settings.p.html"
    conn = connect_db()
    setting_state = dict(fetch_settings(conn))
    if request.method == "POST":
        setting = next(
            (
                (key, value)
                for key, value in request.form.items()
                if re.search("hx_", key)
            ),
            None,
        )
        if setting:
            update_settings(conn, setting)
            flash("Setting updated successfully", "success")
            return render_template("flash.p.html")
    if htmx:
        return render_template(partial_template, settings=setting_state)
    return render_template(
        "base.html", partial_template=partial_template, settings=setting_state
    )


@app.route("/delete_data", methods=["POST"])
def delete_data():
    if request.method == "POST":
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
            flash("Database deleted successfully", "success")
        init_db()
    return render_template("flash.p.html")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def connect_db():
    db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    if exception:
        print(exception)
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    if not os.path.isfile(DATABASE):
        db = g._database = sqlite3.connect(DATABASE)
        with app.app_context():
            with app.open_resource("schema.sql", mode="r") as f:
                db.cursor().executescript(f.read())
            db.commit()


def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    if cursor.fetchone()[0] == 1:
        return True
    return False


def update_settings(conn, setting):
    cursor = conn.cursor()
    name, value = setting
    cursor.execute(
        "INSERT OR REPLACE INTO settings (setting_name, setting_value) VALUES (?, ?)",
        (name, value),
    )
    conn.commit()


def fetch_settings(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings")
    return cursor.fetchall()


def fetch_winners(conn):
    cursor = conn.cursor()
    return cursor.execute(
        """
        SELECT winners.*, prizes_won.*
        FROM winners
        LEFT JOIN prizes_won ON winners.prize = prizes_won.id
        """,
    ).fetchall()


def remove_entry(conn, name, prize):
    cursor = conn.cursor()
    hx_remove_winner = cursor.execute(
        "SELECT setting_value FROM settings WHERE setting_name = 'hx_remove_winner'"
    ).fetchone()
    if hx_remove_winner[0] == "on":
        cursor.execute("DELETE FROM names WHERE id = ?", (name[0],))
        if prize is not None:
            cursor.execute("DELETE FROM prizes WHERE id = ?", (prize[0],))
        conn.commit()


def log_winner(conn, name, prize):
    cursor = conn.cursor()
    hx_log_winner = cursor.execute(
        "SELECT setting_value FROM settings WHERE setting_name = 'hx_log_winner'"
    ).fetchone()
    if hx_log_winner[0] == "on" and name is not None:
        cursor.execute(
            "INSERT INTO winners SELECT *, ? FROM names WHERE id = ?",
            (prize[0] if prize else None, name[0]),
        )
        if prize is not None:
            cursor.execute(
                "INSERT INTO prizes_won SELECT * FROM prizes WHERE id = ?", (prize[0],)
            )
        conn.commit()


def import_data(conn, data, data_type):
    conn.execute(f"DELETE FROM {data_type}")
    total_rows = data.to_sql(data_type, conn, if_exists="append", index_label="id")
    conn.commit()
    return total_rows
