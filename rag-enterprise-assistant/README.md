# RAG Enterprise Assistant

Assistant de questions-reponses sur des documents internes, base sur le principe **RAG** (Retrieval-Augmented Generation) : l'application retrouve les passages les plus pertinents dans vos documents, puis un LLM redige la reponse a partir de ces passages uniquement.

## Fonctionnalites
- Indexation de documents `.txt` / `.md` (decoupage en chunks avec chevauchement)
- Recherche semantique dans une base vectorielle (ChromaDB)
- Reponse redigee par Claude (optionnel) avec citation des fichiers sources
- Mode sans cle API : affiche directement les passages les plus pertinents
- Interface web simple : poser une question, ajouter un document
- API REST (FastAPI) : `/api/ask`, `/api/upload`, `/api/health`
- Conteneurisation Docker

## Architecture
```
documents/*.txt --> decoupage (chunks) --> embeddings --> ChromaDB
                                                             |
question --> recherche des 4 passages les plus proches <-----+
                       |
                       v
           LLM (Claude) ou mode extractif --> reponse + sources
```

## Stack technique
Python, FastAPI, ChromaDB, Anthropic API (optionnel), HTML/JavaScript, Docker

## Installation

```bash
git clone https://github.com/mohamed-makkari/rag-enterprise-assistant.git
cd rag-enterprise-assistant
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac : source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Ouvrir http://localhost:8000

Au premier lancement, le modele d'embeddings (~80 Mo) est telecharge automatiquement (connexion internet requise).

### Activer le LLM (optionnel)
```bash
copy .env.example .env         # Linux/Mac : cp .env.example .env
```
Renseignez `ANTHROPIC_API_KEY` dans `.env`. Ne publiez jamais ce fichier (il est ignore par `.gitignore`).

### Avec Docker
```bash
docker compose up --build
```

## Utilisation
1. Placez vos fichiers dans `documents/` (ils sont indexes au demarrage) ou envoyez-les depuis l'interface.
2. Posez une question, par exemple : *"Combien de jours de conge par an ?"*
3. Les fichiers sources utilises sont affiches sous la reponse.

## Structure
```
app/
  main.py        # API FastAPI
  rag.py         # chunking, indexation, recherche, generation
  static/        # interface web
documents/       # documents d'exemple
ingest.py        # indexation manuelle
```

## Pistes d'amelioration
- Support PDF / DOCX
- Evaluation de la pertinence sur un jeu de questions de test
- Interface React, authentification
