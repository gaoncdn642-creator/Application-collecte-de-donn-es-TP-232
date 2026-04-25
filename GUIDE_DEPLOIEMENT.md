# 🚀 Guide de Déploiement — EduData Cameroun v3.0
## Supabase (Backend + BD) + Netlify (Frontend)

---

## ÉTAPE 1 — Créer la base de données Supabase (GRATUIT, sans carte)

1. Va sur **https://supabase.com** → créer un compte gratuit
2. Clique **"New Project"** → nom : `edudata-cameroun`
3. Choisis un mot de passe fort → **"Create new project"**
4. Attends ~2 minutes que le projet se crée

### Créer les tables SQL

Dans Supabase → **SQL Editor** → colle et exécute ce code :

```sql
-- Table principale des écoles
CREATE TABLE ecoles (
  id BIGSERIAL PRIMARY KEY,
  nom TEXT NOT NULL,
  code_minesec TEXT,
  type_ecole TEXT,
  cycle TEXT,
  langue TEXT,
  milieu TEXT,
  region TEXT,
  departement TEXT,
  ville TEXT,
  quartier TEXT,
  adresse TEXT,
  latitude FLOAT,
  longitude FLOAT,
  nb_eleves INT DEFAULT 0,
  nb_filles INT DEFAULT 0,
  nb_garcons INT DEFAULT 0,
  nb_ens INT DEFAULT 0,
  nb_titulaires INT DEFAULT 0,
  nb_vacataires INT DEFAULT 0,
  nb_salles INT DEFAULT 0,
  nb_niveaux INT DEFAULT 0,
  annee_creation INT,
  acces_eau BOOLEAN DEFAULT FALSE,
  acces_electricite BOOLEAN DEFAULT FALSE,
  acces_internet BOOLEAN DEFAULT FALSE,
  latrines BOOLEAN DEFAULT FALSE,
  bibliotheque BOOLEAN DEFAULT FALSE,
  salle_info BOOLEAN DEFAULT FALSE,
  terrain_sport BOOLEAN DEFAULT FALSE,
  cantine BOOLEAN DEFAULT FALSE,
  responsable TEXT,
  telephone TEXT,
  email TEXT,
  enqueteur TEXT,
  date_collecte TEXT,
  statut TEXT DEFAULT 'Non vérifié',
  observations TEXT,
  collecteur TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des profils utilisateurs
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  nom TEXT,
  email TEXT,
  role TEXT DEFAULT 'Collecteur de données',
  institution TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table des logs d'activité
CREATE TABLE logs (
  id BIGSERIAL PRIMARY KEY,
  action TEXT,
  detail TEXT,
  user TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activer RLS (Row Level Security)
ALTER TABLE ecoles ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Politiques : tout utilisateur connecté peut tout faire
CREATE POLICY "Accès complet authentifiés" ON ecoles FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Accès profils" ON profiles FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Accès logs" ON logs FOR ALL USING (auth.role() = 'authenticated');
```

---

## ÉTAPE 2 — Récupérer les clés Supabase

1. Dans Supabase → **Settings** → **API**
2. Copie les deux valeurs :
   - **Project URL** → ex: `https://abcdef.supabase.co`
   - **anon public key** → ex: `eyJhbGci...`

---

## ÉTAPE 3 — Créer le premier compte utilisateur

1. Dans Supabase → **Authentication** → **Users**
2. Clique **"Add user"** → **"Create new user"**
3. Entre l'email et le mot de passe de l'admin
4. Répète pour chaque collecteur (min. 3 personnes)

---

## ÉTAPE 4 — Configurer l'application

1. Ouvre le fichier `EduData_Cameroun_v3.html` dans un navigateur
2. Va dans **⚙️ Paramètres** → section **Config Supabase**
3. Entre :
   - **URL Supabase** : `https://abcdef.supabase.co`
   - **Clé Anon** : `eyJhbGci...`
4. Clique **"Sauvegarder la config"**
5. Recharge la page → connecte-toi avec ton email/mot de passe

---

## ÉTAPE 5 — Déployer sur Netlify (GRATUIT)

1. Va sur **https://netlify.com** → créer un compte
2. Dashboard → **"Add new site"** → **"Deploy manually"**
3. **Glisse le fichier** `EduData_Cameroun_v3.html` dans la zone
4. Ton site est en ligne en 30 secondes !
5. Renomme le site : **Site configuration** → **Change site name**
   → ex: `edudata-cameroun` → URL finale : `https://edudata-cameroun.netlify.app`

---

## ✅ Résultat final

- 🌐 **Frontend** : `https://edudata-cameroun.netlify.app`
- 🗄️ **Backend + BD** : Supabase (PostgreSQL)
- 👥 **Multi-utilisateurs** : Chaque collecteur se connecte avec son email
- 🔒 **Sécurisé** : Authentification Supabase
- 📊 **Données partagées** : Tout le monde voit les données de toute l'équipe

---

## 👥 Partager avec l'équipe

Envoie simplement l'URL Netlify à tes collègues :
```
https://edudata-cameroun.netlify.app
```
Chaque personne se connecte avec les identifiants créés à l'Étape 3.
