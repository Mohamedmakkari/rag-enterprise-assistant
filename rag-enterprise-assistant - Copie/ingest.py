"""Indexe manuellement le dossier documents/ : python ingest.py"""
from app.rag import ingest_folder

for name, n in ingest_folder().items():
    print(f"{name} -> {n} chunks")
print("Termine.")
