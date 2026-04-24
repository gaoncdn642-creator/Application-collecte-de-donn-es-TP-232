"""
EduData Cameroun — Backend API
Flask + SQLAlchemy + PostgreSQL/SQLite
"""

from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime
import os, csv, io, json, hashlib, secrets

app = Flask(__name__)
CORS(app, origins=["*"])

# ─── CONFIG ───────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///edudata.db")
# Fix Heroku/Render postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ─── MODELS ───────────────────────────────────────────────
class Ecole(db.Model):
    __tablename__ = "ecoles"

    id               = db.Column(db.Integer, primary_key=True)
    nom              = db.Column(db.String(255), nullable=False)
    code_minesec     = db.Column(db.String(50))
    type_ecole       = db.Column(db.String(50))   # Publique / Privée / Confessionnelle ...
    cycle            = db.Column(db.String(80))
    langue           = db.Column(db.String(30))
    milieu           = db.Column(db.String(20))

    # Localisation
    region           = db.Column(db.String(50))
    departement      = db.Column(db.String(80))
    ville            = db.Column(db.String(100))
    quartier         = db.Column(db.String(100))
    adresse          = db.Column(db.String(255))
    latitude         = db.Column(db.Float)
    longitude        = db.Column(db.Float)

    # Effectifs
    nb_eleves        = db.Column(db.Integer, default=0)
    nb_filles        = db.Column(db.Integer, default=0)
    nb_garcons       = db.Column(db.Integer, default=0)
    nb_enseignants   = db.Column(db.Integer, default=0)
    nb_titulaires    = db.Column(db.Integer, default=0)
    nb_vacataires    = db.Column(db.Integer, default=0)
    nb_salles        = db.Column(db.Integer, default=0)
    nb_niveaux       = db.Column(db.Integer, default=0)
    annee_creation   = db.Column(db.Integer)

    # Infrastructures (booleans)
    acces_eau        = db.Column(db.Boolean, default=False)
    acces_electricite= db.Column(db.Boolean, default=False)
    acces_internet   = db.Column(db.Boolean, default=False)
    latrines         = db.Column(db.Boolean, default=False)
    bibliotheque     = db.Column(db.Boolean, default=False)
    salle_info       = db.Column(db.Boolean, default=False)
    terrain_sport    = db.Column(db.Boolean, default=False)
    cantine          = db.Column(db.Boolean, default=False)

    # Contact
    responsable      = db.Column(db.String(150))
    telephone        = db.Column(db.String(30))
    email            = db.Column(db.String(150))
    enqueteur        = db.Column(db.String(150))

    # Meta
    date_collecte    = db.Column(db.String(20))
    statut           = db.Column(db.String(30), default="Non vérifié")
    observations     = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns
                if c.name not in ("created_at", "updated_at")}

    def to_dict_full(self):
        d = self.to_dict()
        d["created_at"] = self.created_at.isoformat() if self.created_at else None
        d["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        return d


class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    password_hash= db.Column(db.String(128))
    role         = db.Column(db.String(30), default="collecteur")
    nom          = db.Column(db.String(150))
    institution  = db.Column(db.String(150))
    region_assignee = db.Column(db.String(50))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        return {"id":self.id,"username":self.username,"role":self.role,
                "nom":self.nom,"institution":self.institution,"region_assignee":self.region_assignee}


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id         = db.Column(db.Integer, primary_key=True)
    action     = db.Column(db.String(50))
    detail     = db.Column(db.String(255))
    user       = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id":self.id,"action":self.action,"detail":self.detail,
                "user":self.user,"created_at":self.created_at.isoformat()}


# ─── HELPERS ──────────────────────────────────────────────
def log_action(action, detail, user="system"):
    entry = ActivityLog(action=action, detail=detail, user=user)
    db.session.add(entry)
    db.session.commit()

def success(data=None, message="OK", code=200):
    return jsonify({"success": True, "message": message, "data": data}), code

def error(message="Erreur", code=400):
    return jsonify({"success": False, "message": message}), code


# ─── ROUTES: HEALTH ───────────────────────────────────────
@app.route("/")
def index():
    return success({"name": "EduData Cameroun API", "version": "2.0",
                    "status": "running", "time": datetime.utcnow().isoformat()})

@app.route("/api/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return success({"db": "connected", "uptime": "OK"})
    except Exception as e:
        return error(f"DB Error: {str(e)}", 500)


# ─── ROUTES: ECOLES ───────────────────────────────────────
@app.route("/api/ecoles", methods=["GET"])
def get_ecoles():
    # Filters
    q       = request.args.get("q", "").strip()
    region  = request.args.get("region", "")
    type_e  = request.args.get("type", "")
    cycle   = request.args.get("cycle", "")
    statut  = request.args.get("statut", "")
    page    = int(request.args.get("page", 1))
    per_page= int(request.args.get("per_page", 20))
    sort    = request.args.get("sort", "created_at")
    order   = request.args.get("order", "desc")

    query = Ecole.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Ecole.nom.ilike(like), Ecole.ville.ilike(like),
                   Ecole.region.ilike(like), Ecole.responsable.ilike(like),
                   Ecole.code_minesec.ilike(like)))
    if region:  query = query.filter(Ecole.region == region)
    if type_e:  query = query.filter(Ecole.type_ecole == type_e)
    if cycle:   query = query.filter(Ecole.cycle == cycle)
    if statut:  query = query.filter(Ecole.statut == statut)

    # Sorting
    sort_col = getattr(Ecole, sort, Ecole.created_at)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    total   = query.count()
    ecoles  = query.paginate(page=page, per_page=per_page, error_out=False)

    return success({
        "items":   [e.to_dict_full() for e in ecoles.items],
        "total":   total,
        "page":    page,
        "pages":   ecoles.pages,
        "per_page": per_page
    })


@app.route("/api/ecoles/<int:id>", methods=["GET"])
def get_ecole(id):
    e = Ecole.query.get_or_404(id)
    return success(e.to_dict_full())


@app.route("/api/ecoles", methods=["POST"])
def create_ecole():
    data = request.get_json()
    if not data:
        return error("Données manquantes")
    if not data.get("nom"):
        return error("Le nom est obligatoire")

    e = Ecole(
        nom              = data.get("nom"),
        code_minesec     = data.get("code_minesec"),
        type_ecole       = data.get("type_ecole"),
        cycle            = data.get("cycle"),
        langue           = data.get("langue"),
        milieu           = data.get("milieu"),
        region           = data.get("region"),
        departement      = data.get("departement"),
        ville            = data.get("ville"),
        quartier         = data.get("quartier"),
        adresse          = data.get("adresse"),
        latitude         = data.get("latitude"),
        longitude        = data.get("longitude"),
        nb_eleves        = int(data.get("nb_eleves") or 0),
        nb_filles        = int(data.get("nb_filles") or 0),
        nb_garcons       = int(data.get("nb_garcons") or 0),
        nb_enseignants   = int(data.get("nb_enseignants") or 0),
        nb_titulaires    = int(data.get("nb_titulaires") or 0),
        nb_vacataires    = int(data.get("nb_vacataires") or 0),
        nb_salles        = int(data.get("nb_salles") or 0),
        nb_niveaux       = int(data.get("nb_niveaux") or 0),
        annee_creation   = data.get("annee_creation"),
        acces_eau        = bool(data.get("acces_eau")),
        acces_electricite= bool(data.get("acces_electricite")),
        acces_internet   = bool(data.get("acces_internet")),
        latrines         = bool(data.get("latrines")),
        bibliotheque     = bool(data.get("bibliotheque")),
        salle_info       = bool(data.get("salle_info")),
        terrain_sport    = bool(data.get("terrain_sport")),
        cantine          = bool(data.get("cantine")),
        responsable      = data.get("responsable"),
        telephone        = data.get("telephone"),
        email            = data.get("email"),
        enqueteur        = data.get("enqueteur"),
        date_collecte    = data.get("date_collecte"),
        statut           = data.get("statut", "Non vérifié"),
        observations     = data.get("observations"),
    )
    db.session.add(e)
    db.session.commit()
    log_action("Création", f'École "{e.nom}" créée', data.get("enqueteur", "inconnu"))
    return success(e.to_dict_full(), "École créée avec succès", 201)


@app.route("/api/ecoles/<int:id>", methods=["PUT"])
def update_ecole(id):
    e = Ecole.query.get_or_404(id)
    data = request.get_json()
    updatable = [
        "nom","code_minesec","type_ecole","cycle","langue","milieu",
        "region","departement","ville","quartier","adresse","latitude","longitude",
        "nb_eleves","nb_filles","nb_garcons","nb_enseignants","nb_titulaires","nb_vacataires",
        "nb_salles","nb_niveaux","annee_creation",
        "acces_eau","acces_electricite","acces_internet","latrines",
        "bibliotheque","salle_info","terrain_sport","cantine",
        "responsable","telephone","email","enqueteur","date_collecte","statut","observations"
    ]
    for field in updatable:
        if field in data:
            setattr(e, field, data[field])
    e.updated_at = datetime.utcnow()
    db.session.commit()
    log_action("Modification", f'École "{e.nom}" modifiée')
    return success(e.to_dict_full(), "École mise à jour")


@app.route("/api/ecoles/<int:id>", methods=["DELETE"])
def delete_ecole(id):
    e = Ecole.query.get_or_404(id)
    nom = e.nom
    db.session.delete(e)
    db.session.commit()
    log_action("Suppression", f'École "{nom}" supprimée')
    return success(message=f'"{nom}" supprimée')


# ─── ROUTES: STATS ────────────────────────────────────────
@app.route("/api/stats")
def get_stats():
    total       = Ecole.query.count()
    total_el    = db.session.query(db.func.sum(Ecole.nb_eleves)).scalar() or 0
    total_ens   = db.session.query(db.func.sum(Ecole.nb_enseignants)).scalar() or 0
    total_filles= db.session.query(db.func.sum(Ecole.nb_filles)).scalar() or 0

    by_region  = dict(db.session.query(Ecole.region, db.func.count()).group_by(Ecole.region).all())
    by_type    = dict(db.session.query(Ecole.type_ecole, db.func.count()).group_by(Ecole.type_ecole).all())
    by_cycle   = dict(db.session.query(Ecole.cycle, db.func.count()).group_by(Ecole.cycle).all())
    by_statut  = dict(db.session.query(Ecole.statut, db.func.count()).group_by(Ecole.statut).all())

    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_count = Ecole.query.filter(Ecole.date_collecte == today).count()

    infra = {}
    for field in ["acces_eau","acces_electricite","acces_internet","latrines","bibliotheque","salle_info","terrain_sport","cantine"]:
        col = getattr(Ecole, field)
        infra[field] = Ecole.query.filter(col == True).count()

    return success({
        "total": total, "total_eleves": total_el,
        "total_enseignants": total_ens, "total_filles": total_filles,
        "today_count": today_count,
        "regions_count": len([v for v in by_region.keys() if v]),
        "ratio_eleves_ens": round(total_el / total_ens, 1) if total_ens else 0,
        "by_region": by_region, "by_type": by_type,
        "by_cycle": by_cycle, "by_statut": by_statut,
        "infra": infra
    })


@app.route("/api/stats/regional")
def stats_regional():
    regions = ["Adamaoua","Centre","Est","Extrême-Nord","Littoral",
               "Nord","Nord-Ouest","Ouest","Sud","Sud-Ouest"]
    result = []
    for r in regions:
        ecoles = Ecole.query.filter_by(region=r).all()
        if not ecoles:
            result.append({"region": r, "count": 0})
            continue
        el  = sum(e.nb_eleves or 0 for e in ecoles)
        ens = sum(e.nb_enseignants or 0 for e in ecoles)
        infra_score = sum([
            sum(1 for e in ecoles if e.acces_eau),
            sum(1 for e in ecoles if e.acces_electricite),
            sum(1 for e in ecoles if e.acces_internet),
            sum(1 for e in ecoles if e.latrines),
        ]) / (len(ecoles) * 4) * 100 if ecoles else 0
        result.append({
            "region": r, "count": len(ecoles),
            "nb_eleves": el, "nb_enseignants": ens,
            "ratio": round(el/ens, 1) if ens else 0,
            "infra_score": round(infra_score, 1),
            "verifie_pct": round(sum(1 for e in ecoles if e.statut=="Vérifié") / len(ecoles) * 100, 1)
        })
    return success(result)


# ─── ROUTES: EXPORT ───────────────────────────────────────
@app.route("/api/export/csv")
def export_csv():
    ecoles = Ecole.query.order_by(Ecole.region, Ecole.nom).all()
    output = io.StringIO()
    w = csv.writer(output, delimiter=";")
    headers = ["ID","Nom","Code MINESEC","Type","Cycle","Langue","Milieu",
               "Région","Département","Ville","Quartier","Élèves","Filles",
               "Garçons","Enseignants","Titulaires","Vacataires","Salles","Niveaux",
               "Création","Eau","Électricité","Internet","Latrines","Biblio",
               "Informatique","Sport","Cantine","Responsable","Téléphone","Email",
               "Enquêteur","Date collecte","Statut","Observations"]
    w.writerow(headers)
    for e in ecoles:
        w.writerow([
            e.id, e.nom, e.code_minesec, e.type_ecole, e.cycle, e.langue, e.milieu,
            e.region, e.departement, e.ville, e.quartier,
            e.nb_eleves, e.nb_filles, e.nb_garcons, e.nb_enseignants,
            e.nb_titulaires, e.nb_vacataires, e.nb_salles, e.nb_niveaux,
            e.annee_creation, e.acces_eau, e.acces_electricite, e.acces_internet,
            e.latrines, e.bibliotheque, e.salle_info, e.terrain_sport, e.cantine,
            e.responsable, e.telephone, e.email, e.enqueteur, e.date_collecte,
            e.statut, e.observations
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(('\ufeff' + output.getvalue()).encode("utf-8")),
        mimetype="text/csv", as_attachment=True,
        download_name="edudata_cameroun.csv"
    )


@app.route("/api/export/json")
def export_json():
    ecoles = Ecole.query.all()
    data = {"export": datetime.utcnow().isoformat(), "total": len(ecoles),
            "source": "EduData Cameroun v2.0",
            "data": [e.to_dict_full() for e in ecoles]}
    output = json.dumps(data, ensure_ascii=False, indent=2)
    return send_file(
        io.BytesIO(output.encode("utf-8")),
        mimetype="application/json", as_attachment=True,
        download_name="edudata_cameroun.json"
    )


# ─── ROUTES: IMPORT ───────────────────────────────────────
@app.route("/api/import/json", methods=["POST"])
def import_json():
    data = request.get_json()
    items = data if isinstance(data, list) else data.get("data", [])
    if not items:
        return error("Fichier vide ou format invalide")
    created = 0
    for item in items:
        item.pop("id", None)
        item.pop("created_at", None)
        item.pop("updated_at", None)
        e = Ecole(**{k: v for k, v in item.items()
                     if k in [c.name for c in Ecole.__table__.columns]})
        db.session.add(e)
        created += 1
    db.session.commit()
    log_action("Import", f"{created} école(s) importée(s)")
    return success({"created": created}, f"{created} école(s) importée(s)")


# ─── ROUTES: USERS ────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data.get("username")).first():
        return error("Ce nom d'utilisateur existe déjà")
    u = User(username=data["username"], role=data.get("role","collecteur"),
             nom=data.get("nom"), institution=data.get("institution"))
    u.set_password(data["password"])
    db.session.add(u)
    db.session.commit()
    return success(u.to_dict(), "Compte créé", 201)


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    u = User.query.filter_by(username=data.get("username")).first()
    if not u or not u.check_password(data.get("password","")):
        return error("Identifiants incorrects", 401)
    token = hashlib.sha256(f"{u.id}{secrets.token_hex(16)}".encode()).hexdigest()
    return success({"user": u.to_dict(), "token": token}, "Connexion réussie")


# ─── ROUTES: LOGS ─────────────────────────────────────────
@app.route("/api/logs")
def get_logs():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    return success([l.to_dict() for l in logs])


# ─── INIT DB ──────────────────────────────────────────────
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="administrateur", nom="Administrateur")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DEBUG", "false").lower() == "true")
