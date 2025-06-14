#!/bin/bash

# Crée le dossier logs s'il n'existe pas
mkdir -p logs

source .venv/bin/activate

# Lance l'application
PYTHONPATH=$PYTHONPATH:. python src/generic/main.py
