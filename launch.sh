#!/bin/bash

# Installation des dépendances
echo "Installing dependencies..."
pip install -r requirements.txt

# Crée le dossier logs s'il n'existe pas
mkdir -p logs

# Variables d'environnement pour Replit
export PYTHONPATH=$PYTHONPATH:.

# Lance l'application
echo "Starting Hyperliquid Trading Bot..."
python src/generic/main.py
