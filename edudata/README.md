# 📚 EduData Cameroun v2.1 — Application Full-Stack

## Architecture

```
frontend/           → HTML/CSS/JS + Chart.js (déployé sur Vercel)
    index.html      → Interface complète + appels API fetch()

backend/            → Python Flask REST API (déployé sur Vercel)
    app.py          → API + modèles SQLAlchemy
    requirements.txt
    .env.example    → Variables d'environnement
```

---

## 🗄️ Base de données — Modèles

### Table `ecoles` (35 colonnes)
- Identification : nom, code_minesec, type_ecole, cycle, langue, milieu
- Localisation : region, departement, ville, quartier, adresse, latitude, longitude
- Effectifs : nb_eleves, nb_filles, nb_garcons, nb_enseignants, nb_titulaires, nb_vacataires, nb_salles, nb_niveaux, annee_creation
- Infrastructures (8 boolean) : acces_eau, acces_electricite, acces_internet, latrines, bibliotheque, salle_info, terrain_sport, cantine
- Contact : responsable, telephone, email, enqueteur
- Meta : date_collecte, statut, observations, created_at, updated_at

### Table `users`
- username, password_hash (SHA256), role, nom, institution, region_assignee

### Table `activity_logs`
- action, detail, user, created_at

---

## 🔌 API REST — Endpoints

| Méthode | Endpoint              | Description                         |
|---------|-----------------------|-------------------------------------|
| GET     | `/api/health`         | Santé de l'API + base de données    |
| GET     | `/api/ecoles`         | Liste avec pagination, filtres, tri |
| GET     | `/api/ecoles/:id`     | Détail d'une école                  |
| POST    | `/api/ecoles`         | Créer une école                     |
| PUT     | `/api/ecoles/:id`     | Modifier une école                  |
| DELETE  | `/api/ecoles/:id`     | Supprimer une école                 |
| GET     | `/api/stats`          | Statistiques globales               |
| GET     | `/api/stats/regional` | Stats détaillées par région         |
| GET     | `/api/export/csv`     | Export CSV                          |
| GET     | `/api/export/json`    | Export JSON                         |
| POST    | `/api/import/json`    | Import JSON                         |
| POST    | `/api/auth/login`     | Connexion utilisateur               |
| POST    | `/api/auth/register`  | Inscription                         |
| GET     | `/api/logs`           | Journal d'activité                  |

---

## 🚀 DÉPLOIEMENT SUR VERCEL (Backend + Frontend)

### Prérequis
- Un compte gratuit sur **https://vercel.com**
- Une base PostgreSQL gratuite sur **https://neon.tech**

---

### ÉTAPE 1 — Créer la base de données PostgreSQL sur Neon

1. Va sur **https://neon.tech** → créer un compte gratuit
2. Clique **"New Project"** → nom : `edudata-cameroun`
3. Copie la **Connection String** qui ressemble à :
   ```
   postgresql://user:password@host.neon.tech/edudata?sslmode=require
   ```
4. Garde cette URL pour l'étape suivante

---

### ÉTAPE 2 — Déployer le BACKEND sur Vercel

**1. Crée un fichier `backend/vercel.json`** avec ce contenu :
```json
{
  "version": 2,
  "builds": [{ "src": "app.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

**2. Déploie via l'interface Vercel :**
1. Va sur **https://vercel.com** → **"Add New Project"**
2. Clique **"Upload"** → glisse-dépose le dossier `backend/`
3. Dans **"Environment Variables"**, ajoute :
   - `DATABASE_URL` → ta connection string Neon
   - `SECRET_KEY` → une phrase secrète longue (ex: `edudata_cameroun_secret_2024`)
4. Clique **"Deploy"**
5. Ton API sera à : `https://edudata-api-xxxx.vercel.app`

**OU déploie via la CLI :**
```bash
npm install -g vercel   # installer Vercel CLI
cd backend
vercel login
vercel env add DATABASE_URL   # coller la connection string Neon
vercel env add SECRET_KEY     # taper une clé secrète
vercel --prod
```

**3. Teste** en ouvrant dans le navigateur :
```
https://edudata-api-xxxx.vercel.app/api/health
```
Tu dois voir : `{"success": true, "data": {"db": "connected"}}`

---

### ÉTAPE 3 — Déployer le FRONTEND sur Vercel

**1. Déploie via l'interface Vercel :**
1. Retourne sur **https://vercel.com** → **"Add New Project"**
2. Clique **"Upload"** → glisse-dépose le dossier `frontend/`
3. Aucune variable d'environnement requise
4. Clique **"Deploy"**
5. Ton site sera à : `https://edudata-front-xxxx.vercel.app`

**OU déploie via la CLI :**
```bash
cd frontend
vercel --prod
```

**2. Personnaliser l'URL (optionnel) :**
- Dashboard Vercel → ton projet frontend → **Settings** → **Domains**
- Change le nom en `edudata-cameroun`
- Ton site sera à : `https://edudata-cameroun.vercel.app`

---

### ÉTAPE 4 — Connecter Frontend ↔ Backend

1. Ouvre ton application : `https://edudata-cameroun.vercel.app`
2. Connecte-toi : `admin` / `admin123`
3. Va dans **⚙️ Paramètres** → **API Backend**
4. Entre l'URL de ton backend :
   ```
   https://edudata-api-xxxx.vercel.app
   ```
5. Clique **"Enregistrer"** puis **"Tester la connexion"**
6. ✅ Le voyant passe au vert — l'application est opérationnelle !

---

## 💻 LANCEMENT EN LOCAL

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Édite .env avec tes variables
python app.py
# API sur http://localhost:5000

# Frontend
# Ouvre frontend/index.html dans le navigateur
# Paramètres → URL API → http://localhost:5000
```

---

## 🔑 Compte par défaut
- **Username** : admin
- **Password** : admin123

> ⚠️ Changez le mot de passe en production !

---

## 📊 Graphiques disponibles

| Graphique            | Description                                  |
|----------------------|----------------------------------------------|
| Doughnut             | Répartition par type (dashboard)             |
| Barres horizontales  | Taux d'infrastructure (dashboard)            |
| Barres verticales    | Nombre d'écoles par région (dashboard)       |
| Pie chart            | Types d'établissements                       |
| Semi-doughnut        | Statuts de vérification                      |
| Semi-doughnut        | Milieu urbain / rural                        |
| Radar                | Score infrastructure par région (top 6)      |
| Polar area           | Répartition régionale                        |
| Barres empilées      | Élèves filles / garçons par région           |
| Courbe               | Évolution des collectes dans le temps        |
| Barres groupées      | Infrastructures par région (top 5)           |
| Bulles (Bubble)      | Élèves vs Enseignants par région             |

---

## ✅ Fonctionnalités

- 🔐 Authentification login / logout
- 📊 Tableau de bord avec statistiques live
- 📈 Analytiques avancées (KPI, ratios, tableau régional)
- 🎯 Page graphiques avec 9 types de visualisations
- 🗺️ Carte schématique interactive du Cameroun
- ➕ Formulaire en 4 étapes (toggles corrigés)
- 📋 Base de données avec filtres, tri, pagination
- ⬇️ Export CSV et JSON
- ⬆️ Import JSON avec drag & drop
- 📜 Journal d'activité
- ⚙️ Configuration URL API dynamique
- 🗄️ API REST complète (14 endpoints)
- 🐘 PostgreSQL en production / SQLite en développement
