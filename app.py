# ============================================================
#  DermaNova Medical Platform — app.py
#  Auteur : Projet 1TA ENSTAB  |  Framework : Flask + VGG16
# ============================================================

import os, io, json, base64
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
# ── Importation conditionnelle TensorFlow & NumPy ────────────
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image as keras_image
    import numpy as np
    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False

import sqlite3

# ── Importation conditionnelle MySQL ─────────────────────────
try:
    import mysql.connector
    DB_TYPE = "mysql"
except ImportError:
    DB_TYPE = "sqlite"

# ── Importation conditionnelle ReportLab (PDF) ───────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ============================================================
#  CONFIGURATION
# ============================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "DermaNova-Secret-2025-ENSTAB!")

UPLOAD_FOLDER   = os.path.join("static", "uploads")
ALLOWED_EXT     = {"png", "jpg", "jpeg", "bmp", "webp"}
MAX_CONTENT_MB  = 10
MODEL_PATH      = os.path.join("model", "vgg16_skin_cancer.h5")
IMG_SIZE        = (224, 224)

app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Config base de données ────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "user":     os.environ.get("DB_USER",     "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "dermanovadb"),
}
SQLITE_PATH = os.path.join(app.root_path, "DermaNova.db")

# ============================================================
#  HELPERS BASE DE DONNÉES
# ============================================================
def get_db():
    """Retourne une connexion DB (MySQL ou SQLite selon l'env)."""
    global DB_TYPE
    if DB_TYPE == "mysql":
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except Exception:
            DB_TYPE = "sqlite"
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite():
    """Crée les tables SQLite si elles n'existent pas."""
    conn = sqlite3.connect(SQLITE_PATH)
    cur  = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            full_name  TEXT,
            role       TEXT DEFAULT 'user',
            avatar     TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        );
        CREATE TABLE IF NOT EXISTS patients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT NOT NULL,
            age         INTEGER,
            gender      TEXT DEFAULT 'Autre',
            result      TEXT NOT NULL,
            probability REAL NOT NULL,
            image_path  TEXT NOT NULL,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL,
            subject    TEXT,
            message    TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    admin_pw = generate_password_hash("Admin1234")
    demo_pw  = generate_password_hash("Doctor123")
    cur.execute("INSERT OR IGNORE INTO users (username,email,password,full_name,role) VALUES (?,?,?,?,?)",
                ("admin","admin@DermaNova.tn", admin_pw, "Administrateur DermaNova", "admin"))
    cur.execute("INSERT OR IGNORE INTO users (username,email,password,full_name,role) VALUES (?,?,?,?,?)",
                ("dr_demo","demo@DermaNova.tn", demo_pw, "Dr. Demo Médecin", "doctor"))
    conn.commit()
    conn.close()

def _mysql_add_column_if_missing(cur, conn, table, column, definition):
    """Helper : ajoute une colonne MySQL si elle n'existe pas encore."""
    cur.execute(f"SHOW COLUMNS FROM `{table}` LIKE '{column}'")
    if not cur.fetchone():
        print(f"[DermaNova] ⚠️  Colonne '{column}' manquante dans '{table}'. Migration en cours...")
        try:
            cur.execute(f"ALTER TABLE `{table}` ADD COLUMN {column} {definition}")
            conn.commit()
            print(f"[DermaNova] ✅ Colonne '{column}' ajoutée avec succès.")
        except Exception as ex:
            print(f"[DermaNova] ❌ Erreur migration '{column}' : {ex}")

def init_db():
    """Initialise et migre la base de données SQLite ou MySQL."""
    global DB_TYPE
    # Toujours initialiser SQLite par sécurité
    init_sqlite()

    if DB_TYPE == "mysql":
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cur  = conn.cursor()

            # ── Vérifier si la table users existe ────────────
            cur.execute("SHOW TABLES LIKE 'users'")
            table_exists = cur.fetchone()

            if table_exists:
                # ── Migration : ajouter toutes les colonnes manquantes ──
                _mysql_add_column_if_missing(cur, conn, "users", "email",      "VARCHAR(100) UNIQUE")
                _mysql_add_column_if_missing(cur, conn, "users", "full_name",  "VARCHAR(100) DEFAULT NULL")
                _mysql_add_column_if_missing(cur, conn, "users", "role",       "VARCHAR(20) DEFAULT 'user'")
                _mysql_add_column_if_missing(cur, conn, "users", "avatar",     "VARCHAR(255) DEFAULT NULL")
                _mysql_add_column_if_missing(cur, conn, "users", "last_login", "DATETIME DEFAULT NULL")
            else:
                # ── Créer les tables complètes ────────────────
                print("[DermaNova] ⚠️  Table 'users' absente. Création en cours...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id         INT AUTO_INCREMENT PRIMARY KEY,
                        username   VARCHAR(50) UNIQUE NOT NULL,
                        email      VARCHAR(100) UNIQUE NOT NULL,
                        password   VARCHAR(255) NOT NULL,
                        full_name  VARCHAR(100) DEFAULT NULL,
                        role       VARCHAR(20) DEFAULT 'user',
                        avatar     VARCHAR(255) DEFAULT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME DEFAULT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS patients (
                        id          INT AUTO_INCREMENT PRIMARY KEY,
                        user_id     INT NOT NULL,
                        name        VARCHAR(100) NOT NULL,
                        age         INT DEFAULT NULL,
                        gender      VARCHAR(20) DEFAULT 'Autre',
                        result      VARCHAR(20) NOT NULL,
                        probability FLOAT NOT NULL,
                        image_path  VARCHAR(255) NOT NULL,
                        notes       TEXT DEFAULT NULL,
                        created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                        id         INT AUTO_INCREMENT PRIMARY KEY,
                        name       VARCHAR(100) NOT NULL,
                        email      VARCHAR(100) NOT NULL,
                        subject    VARCHAR(150) DEFAULT NULL,
                        message    TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                """)
                conn.commit()

                # Seed admin accounts
                admin_pw = generate_password_hash("Admin1234")
                demo_pw  = generate_password_hash("Doctor123")
                try:
                    cur.execute(
                        "INSERT IGNORE INTO users (id,username,email,password,full_name,role) VALUES (%s,%s,%s,%s,%s,%s)",
                        (1, "admin", "admin@DermaNova.tn", admin_pw, "Administrateur DermaNova", "admin"))
                    cur.execute(
                        "INSERT IGNORE INTO users (id,username,email,password,full_name,role) VALUES (%s,%s,%s,%s,%s,%s)",
                        (2, "dr_demo", "demo@DermaNova.tn", demo_pw, "Dr. Demo Médecin", "doctor"))
                    conn.commit()
                except Exception:
                    pass
                print("[DermaNova] ✅ Tables MySQL créées avec succès.")

            conn.close()
        except Exception as e:
            print(f"[DermaNova] ⚠️  Erreur MySQL init/migration : {e}")
            print("[DermaNova] Passage en mode de repli SQLite.")
            DB_TYPE = "sqlite"

# ============================================================
#  CHARGEMENT DU MODÈLE IA
# ============================================================
model = None
def load_ai_model():
    global model
    if TF_AVAILABLE and os.path.exists(MODEL_PATH):
        try:
            model = load_model(MODEL_PATH)
            print(f"[DermaNova] Model loaded: {MODEL_PATH}")
        except Exception as e:
            print(f"[DermaNova] ⚠️  Erreur chargement modèle : {e}")
    else:
        print("[DermaNova] INFO Model not found - demo mode enabled.")

# ============================================================
#  DÉCORATEURS
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ============================================================
#  UTILITAIRES
# ============================================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def predict_image(filepath):
    """
    Prédit la classe d'une image médicale.
    Retourne (label, probabilité) ou mode démo si modèle absent.
    """
    if model is not None and TF_AVAILABLE:
        img  = keras_image.load_img(filepath, target_size=IMG_SIZE)
        arr  = keras_image.img_to_array(img) / 255.0
        arr  = np.expand_dims(arr, axis=0)
        pred = float(model.predict(arr, verbose=0)[0][0])
        label = "Malignant" if pred > 0.5 else "Benign"
        return label, pred if pred > 0.5 else 1 - pred
    import random
    prob  = round(random.uniform(0.55, 0.97), 4)
    label = random.choice(["Benign", "Malignant"])
    return label, prob

def get_stats(user_id=None):
    """Statistiques pour le dashboard."""
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            where  = "WHERE user_id=%s" if user_id else ""
            params = (user_id,) if user_id else ()

            cur.execute(f"SELECT COUNT(*) AS total FROM patients {where}", params)
            total = cur.fetchone()["total"]

            and_or = "AND" if user_id else "WHERE"
            cur.execute(
                f"SELECT COUNT(*) AS mal FROM patients {where} {and_or} result='Malignant'",
                params)
            mal = cur.fetchone()["mal"]
        else:
            cur = conn.cursor()
            if user_id:
                cur.execute("SELECT COUNT(*) FROM patients WHERE user_id=?", (user_id,))
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM patients WHERE user_id=? AND result='Malignant'", (user_id,))
                mal = cur.fetchone()[0]
            else:
                cur.execute("SELECT COUNT(*) FROM patients")
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM patients WHERE result='Malignant'")
                mal = cur.fetchone()[0]

        ben  = total - mal
        rate = round((mal / total * 100), 1) if total else 0
        return {"total": total, "malignant": mal, "benign": ben, "detection_rate": rate}
    finally:
        conn.close()

# ============================================================
#  ROUTES — PAGES PUBLIQUES
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name    = request.form.get("name","").strip()
        email   = request.form.get("email","").strip()
        subject = request.form.get("subject","").strip()
        message = request.form.get("message","").strip()
        if not all([name, email, message]):
            flash("Veuillez remplir tous les champs obligatoires.", "danger")
            return render_template("contact.html")
        conn = get_db()
        try:
            if DB_TYPE == "mysql":
                cur = conn.cursor()
                cur.execute("INSERT INTO contacts(name,email,subject,message) VALUES(%s,%s,%s,%s)",
                            (name, email, subject, message))
            else:
                cur = conn.cursor()
                cur.execute("INSERT INTO contacts(name,email,subject,message) VALUES(?,?,?,?)",
                            (name, email, subject, message))
            conn.commit()
            flash("Message envoyé avec succès ! Nous vous répondrons sous 24h.", "success")
            return redirect(url_for("contact"))
        finally:
            conn.close()
    return render_template("contact.html")

# ============================================================
#  ROUTES — AUTHENTIFICATION
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        conn = get_db()
        try:
            if DB_TYPE == "mysql":
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, username))
                user = cur.fetchone()
            else:
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username=? OR email=?", (username, username))
                row = cur.fetchone()
                user = dict(row) if row else None

            if user and check_password_hash(user["password"], password):
                session.update({
                    "user_id":   user["id"],
                    "username":  user["username"],
                    "full_name": user.get("full_name") or user["username"],
                    "role":      user.get("role", "user"),
                    "email":     user.get("email", ""),
                })
                if DB_TYPE == "mysql":
                    cur.execute("UPDATE users SET last_login=NOW() WHERE id=%s", (user["id"],))
                else:
                    cur.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user["id"],))
                conn.commit()
                flash(f"Bienvenue, {session['full_name']} ! 👋", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Identifiants incorrects. Veuillez réessayer.", "danger")
        finally:
            conn.close()
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username  = request.form.get("username","").strip()
        email     = request.form.get("email","").strip()
        full_name = request.form.get("full_name","").strip()
        password  = request.form.get("password","")
        confirm   = request.form.get("confirm_password","")

        if not all([username, email, password, confirm]):
            flash("Tous les champs sont obligatoires.", "danger")
            return render_template("register.html")
        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
            return render_template("register.html")

        conn = get_db()
        try:
            hashed = generate_password_hash(password)
            if DB_TYPE == "mysql":
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users(username,email,password,full_name) VALUES(%s,%s,%s,%s)",
                    (username, email, hashed, full_name or None))
            else:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users(username,email,password,full_name) VALUES(?,?,?,?)",
                    (username, email, hashed, full_name or None))
            conn.commit()
            flash("Compte créé avec succès ! Connectez-vous.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            err = str(e).lower()
            if "unique" in err or "duplicate" in err or "1062" in err:
                flash("Ce nom d'utilisateur ou email est déjà utilisé.", "danger")
            else:
                flash(f"Erreur : {e}", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    name = session.get("full_name", "")
    session.clear()
    flash(f"À bientôt, {name} ! Déconnexion réussie.", "info")
    return redirect(url_for("index"))

# ============================================================
#  ROUTES — DASHBOARD
# ============================================================
@app.route("/dashboard")
@login_required
def dashboard():
    uid   = session["user_id"]
    stats = get_stats(uid if session["role"] != "admin" else None)
    conn  = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT p.*, u.full_name AS doctor FROM patients p "
                "LEFT JOIN users u ON p.user_id=u.id "
                + ("WHERE p.user_id=%s " if session["role"] != "admin" else "")
                + "ORDER BY p.created_at DESC LIMIT 5",
                (uid,) if session["role"] != "admin" else ()
            )
            recent = cur.fetchall()
        else:
            cur = conn.cursor()
            if session["role"] == "admin":
                cur.execute(
                    "SELECT p.*, u.full_name AS doctor FROM patients p "
                    "LEFT JOIN users u ON p.user_id=u.id "
                    "ORDER BY p.created_at DESC LIMIT 5"
                )
            else:
                cur.execute(
                    "SELECT p.*, u.full_name AS doctor FROM patients p "
                    "LEFT JOIN users u ON p.user_id=u.id "
                    "WHERE p.user_id=? ORDER BY p.created_at DESC LIMIT 5",
                    (uid,)
                )
            recent = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return render_template("dashboard.html", stats=stats, recent=recent)

# ============================================================
#  ROUTES — PRÉDICTION IA
# ============================================================
@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if request.method == "POST":
        name   = request.form.get("name","").strip()
        age    = request.form.get("age","").strip()
        gender = request.form.get("gender","Autre")
        notes  = request.form.get("notes","").strip()
        file   = request.files.get("image")

        if not file or file.filename == "":
            flash("Veuillez sélectionner une image.", "warning")
            return render_template("predict.html")
        if not allowed_file(file.filename):
            flash("Format non supporté. Utilisez PNG, JPG ou JPEG.", "danger")
            return render_template("predict.html")
        if not name:
            flash("Le nom du patient est obligatoire.", "warning")
            return render_template("predict.html")

        filename = secure_filename(
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        )
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        label, prob = predict_image(filepath)

        conn = get_db()
        try:
            rel_path = f"uploads/{filename}"
            if DB_TYPE == "mysql":
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO patients(user_id,name,age,gender,result,probability,image_path,notes) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (session["user_id"], name, age or None, gender, label, prob, rel_path, notes)
                )
                patient_id = cur.lastrowid
            else:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO patients(user_id,name,age,gender,result,probability,image_path,notes) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (session["user_id"], name, age or None, gender, label, prob, rel_path, notes)
                )
                patient_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()

        flash("Analyse IA terminée avec succès !", "success")
        return redirect(url_for("result", patient_id=patient_id))

    return render_template("predict.html")

@app.route("/result/<int:patient_id>")
@login_required
def result(patient_id):
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
            patient = cur.fetchone()
        else:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
            row = cur.fetchone()
            patient = dict(row) if row else None
    finally:
        conn.close()
    if not patient:
        flash("Analyse introuvable.", "danger")
        return redirect(url_for("dashboard"))
    if session["role"] != "admin" and patient["user_id"] != session["user_id"]:
        flash("Accès non autorisé.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("result.html", patient=patient)

# ============================================================
#  ROUTES — HISTORIQUE PATIENTS
# ============================================================
@app.route("/patients")
@login_required
def patients():
    uid    = session["user_id"]
    search = request.args.get("q","").strip()
    conn   = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            if session["role"] == "admin":
                q      = "SELECT p.*, u.full_name AS doctor FROM patients p LEFT JOIN users u ON p.user_id=u.id"
                params = ()
                if search:
                    q     += " WHERE p.name LIKE %s OR p.result LIKE %s"
                    params = (f"%{search}%", f"%{search}%")
            else:
                q      = "SELECT p.*, u.full_name AS doctor FROM patients p LEFT JOIN users u ON p.user_id=u.id WHERE p.user_id=%s"
                params = (uid,)
                if search:
                    q     += " AND (p.name LIKE %s OR p.result LIKE %s)"
                    params = (uid, f"%{search}%", f"%{search}%")
            q += " ORDER BY p.created_at DESC"
            cur.execute(q, params)
            data = cur.fetchall()
        else:
            cur = conn.cursor()
            if session["role"] == "admin":
                if search:
                    cur.execute(
                        "SELECT p.*, u.full_name AS doctor FROM patients p "
                        "LEFT JOIN users u ON p.user_id=u.id "
                        "WHERE p.name LIKE ? OR p.result LIKE ? ORDER BY p.created_at DESC",
                        (f"%{search}%", f"%{search}%")
                    )
                else:
                    cur.execute(
                        "SELECT p.*, u.full_name AS doctor FROM patients p "
                        "LEFT JOIN users u ON p.user_id=u.id ORDER BY p.created_at DESC"
                    )
            else:
                if search:
                    cur.execute(
                        "SELECT p.*, u.full_name AS doctor FROM patients p "
                        "LEFT JOIN users u ON p.user_id=u.id "
                        "WHERE p.user_id=? AND (p.name LIKE ? OR p.result LIKE ?) ORDER BY p.created_at DESC",
                        (uid, f"%{search}%", f"%{search}%")
                    )
                else:
                    cur.execute(
                        "SELECT p.*, u.full_name AS doctor FROM patients p "
                        "LEFT JOIN users u ON p.user_id=u.id "
                        "WHERE p.user_id=? ORDER BY p.created_at DESC",
                        (uid,)
                    )
            data = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return render_template("patients.html", patients=data, search=search)

@app.route("/patients/delete/<int:pid>", methods=["POST"])
@login_required
def delete_patient(pid):
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM patients WHERE id=%s", (pid,))
            p = cur.fetchone()
        else:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE id=?", (pid,))
            row = cur.fetchone()
            p = dict(row) if row else None
        if not p:
            flash("Introuvable.", "danger")
            return redirect(url_for("patients"))
        if session["role"] != "admin" and p["user_id"] != session["user_id"]:
            flash("Non autorisé.", "danger")
            return redirect(url_for("patients"))
        img = os.path.join("static", p["image_path"])
        if os.path.exists(img):
            os.remove(img)
        if DB_TYPE == "mysql":
            cur2 = conn.cursor()
            cur2.execute("DELETE FROM patients WHERE id=%s", (pid,))
        else:
            cur.execute("DELETE FROM patients WHERE id=?", (pid,))
        conn.commit()
        flash("Analyse supprimée.", "success")
    finally:
        conn.close()
    return redirect(url_for("patients"))

# ============================================================
#  ROUTES — TÉLÉCHARGEMENT PDF
# ============================================================
@app.route("/result/<int:patient_id>/pdf")
@login_required
def download_pdf(patient_id):
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
            p = cur.fetchone()
        else:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
            row = cur.fetchone()
            p = dict(row) if row else None
    finally:
        conn.close()
    if not p:
        flash("Analyse introuvable.", "danger")
        return redirect(url_for("dashboard"))

    if not PDF_AVAILABLE:
        flash("Module PDF non installé. pip install reportlab", "warning")
        return redirect(url_for("result", patient_id=patient_id))

    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # En-tête
    c.setFillColor(colors.HexColor("#0d6efd"))
    c.rect(0, H-80, W, 80, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, H-48, "DermaNova Medical Platform")
    c.setFont("Helvetica", 11)
    c.drawString(40, H-68, "Rapport d'analyse dermatologique par IA")

    # Infos patient
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, H-120, "Informations du patient")
    c.setFont("Helvetica", 11)
    fields = [
        ("Nom",   p.get("name","")),
        ("Âge",   str(p.get("age","")) + " ans" if p.get("age") else "N/A"),
        ("Genre", p.get("gender","N/A")),
        ("Date",  str(p.get("created_at",""))[:19]),
    ]
    y = H - 145
    for label, val in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, f"{label} :")
        c.setFont("Helvetica", 11)
        c.drawString(140, y, val)
        y -= 20

    # Résultat
    result_color = colors.HexColor("#dc3545") if p.get("result") == "Malignant" else colors.HexColor("#198754")
    c.setFillColor(result_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y-20, f"Résultat : {p.get('result','')}")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    prob_pct = round(p.get("probability", 0) * 100, 2)
    c.drawString(40, y-44, f"Confiance : {prob_pct}%")

    # Notes
    if p.get("notes"):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y-80, "Notes cliniques :")
        c.setFont("Helvetica", 10)
        c.drawString(40, y-98, p["notes"][:300])

    # Image
    img_path = os.path.join("static", p.get("image_path",""))
    if os.path.exists(img_path):
        try:
            c.drawImage(img_path, 40, y-260, width=150, height=150, preserveAspectRatio=True)
        except Exception:
            pass

    # Pied de page
    c.setFillColor(colors.HexColor("#6c757d"))
    c.setFont("Helvetica", 9)
    c.drawString(40, 30, "DermaNova — ENSTAB Université de Carthage | Rapport généré automatiquement")
    c.drawRightString(W-40, 30, datetime.now().strftime("%d/%m/%Y %H:%M"))

    c.save()
    buf.seek(0)
    fname = f"DermaNova_rapport_{p.get('name','patient')}_{patient_id}.pdf"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype="application/pdf")

# ============================================================
#  ROUTES — ADMIN
# ============================================================
@app.route("/admin")
@login_required
@admin_required
def admin():
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS c FROM patients")
            total_analyses = cur.fetchone()["c"]
            cur.execute("SELECT * FROM contacts ORDER BY created_at DESC LIMIT 10")
            messages = cur.fetchall()
        else:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT COUNT(*) FROM patients")
            total_analyses = cur.fetchone()[0]
            cur.execute("SELECT * FROM contacts ORDER BY created_at DESC LIMIT 10")
            messages = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    stats = get_stats()
    return render_template("admin.html", users=users, stats=stats,
                           total_analyses=total_analyses, messages=messages)

@app.route("/admin/user/<int:uid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(uid):
    if uid == session["user_id"]:
        flash("Impossible de supprimer son propre compte.", "danger")
        return redirect(url_for("admin"))
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id=%s", (uid,))
        else:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.commit()
        flash("Utilisateur supprimé.", "success")
    finally:
        conn.close()
    return redirect(url_for("admin"))

# ============================================================
#  API JSON — statistiques pour graphiques
# ============================================================
@app.route("/api/stats")
@login_required
def api_stats():
    uid  = session["user_id"]
    role = session["role"]
    conn = get_db()
    try:
        if DB_TYPE == "mysql":
            cur = conn.cursor(dictionary=True)
            q   = "SELECT DATE(created_at) AS d, result, COUNT(*) AS n FROM patients"
            q  += (" WHERE user_id=%s " if role != "admin" else " ")
            q  += "GROUP BY d, result ORDER BY d DESC LIMIT 30"
            cur.execute(q, (uid,) if role != "admin" else ())
            rows = cur.fetchall()
        else:
            cur = conn.cursor()
            if role == "admin":
                cur.execute(
                    "SELECT date(created_at) AS d, result, COUNT(*) AS n "
                    "FROM patients GROUP BY d, result ORDER BY d DESC LIMIT 30"
                )
            else:
                cur.execute(
                    "SELECT date(created_at) AS d, result, COUNT(*) AS n "
                    "FROM patients WHERE user_id=? GROUP BY d, result ORDER BY d DESC LIMIT 30",
                    (uid,)
                )
            rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return jsonify(rows)

# ============================================================
#  GESTION D'ERREURS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", error_code=404,
                           error_msg="Page introuvable"), 404

@app.errorhandler(413)
def too_large(e):
    flash(f"Fichier trop volumineux (max {MAX_CONTENT_MB} Mo).", "danger")
    return redirect(url_for("predict"))

@app.errorhandler(500)
def server_error(e):
    return render_template("base.html", error_code=500,
                           error_msg="Erreur serveur interne"), 500

# ============================================================
#  DÉMARRAGE
# ============================================================
if __name__ == "__main__":
    init_db()
    load_ai_model()
    app.run(debug=True, host="0.0.0.0", port=5000)