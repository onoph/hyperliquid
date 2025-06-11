#!/bin/bash

# Script de nettoyage PythonAnywhere
# Utilisation: bash clean_pythonanywhere.sh

set -e  # Arrêter en cas d'erreur

echo "=== NETTOYAGE PYTHONANYWHERE ==="
echo ""

# Fonction pour afficher les commandes exécutées
run_cmd() {
    echo "Exécution: $*"
    "$@" || true  # Continue même en cas d'erreur
    echo ""
}

# 1. Désactiver l'environnement virtuel (si activé)
echo "1. Désactivation de l'environnement virtuel..."
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Environnement virtuel détecté: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi
echo "✓ Fait"
echo ""

# 2. Supprimer les environnements virtuels
echo "2. Suppression des environnements virtuels..."
run_cmd rm -rf ~/.virtualenvs/mysite-virtualenv/
run_cmd rm -rf .venv/
run_cmd rm -rf venv/
run_cmd rm -rf env/
echo "✓ Environnements virtuels supprimés"

# 3. Nettoyer les caches pip
echo "3. Nettoyage des caches pip..."
run_cmd pip cache purge
run_cmd python3.10 -m pip cache purge
run_cmd python3 -m pip cache purge
run_cmd rm -rf ~/.cache/pip/
echo "✓ Caches pip nettoyés"

# 4. Supprimer les fichiers Python temporaires
echo "4. Suppression des fichiers Python temporaires..."
run_cmd find . -name "*.pyc" -delete
run_cmd find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
run_cmd find ~ -name "*.pyc" -delete 2>/dev/null
run_cmd find ~ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✓ Fichiers temporaires Python supprimés"

# 5. Nettoyer les logs et fichiers temporaires système
echo "5. Nettoyage des fichiers temporaires système..."
run_cmd rm -rf /tmp/pip-*
run_cmd rm -rf /tmp/tmp*
run_cmd rm -rf ~/.local/share/Trash/files/* 2>/dev/null
echo "✓ Fichiers temporaires système nettoyés"

# 6. Nettoyer les packages globaux inutiles (optionnel)
echo "6. Nettoyage des packages globaux (optionnel)..."
echo "Liste des packages installés globalement:"
pip list --user 2>/dev/null || echo "Aucun package utilisateur trouvé"
echo ""

# 7. Vérifier l'espace disque disponible
echo "7. Vérification de l'espace disque..."
echo "Espace disque disponible:"
df -h ~ | head -2
echo ""
echo "Utilisation du répertoire home (top 10):"
du -sh ~/* 2>/dev/null | sort -hr | head -10 || echo "Erreur lors du calcul"
echo ""

echo "=== NETTOYAGE TERMINÉ ==="
echo ""
echo "Prochaines étapes recommandées:"
echo "1. Créer un nouvel environnement virtuel:"
echo "   python3.10 -m venv .venv"
echo ""
echo "2. Activer l'environnement:"
echo "   source .venv/bin/activate"
echo ""
echo "3. Installer les dépendances minimales:"
echo "   pip install -r requirements_prod.txt"
echo ""
echo "4. Vérifier l'installation:"
echo "   pip list"
echo ""

# Optionnel: Recréer automatiquement l'environnement
read -p "Voulez-vous recréer automatiquement l'environnement virtuel? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Création de l'environnement virtuel..."
    python3.10 -m venv .venv
    echo "✓ Environnement virtuel créé"
    
    echo "Activation de l'environnement..."
    source .venv/bin/activate
    echo "✓ Environnement activé"
    
    if [ -f requirements_prod.txt ]; then
        echo "Installation des dépendances..."
        pip install --upgrade pip
        pip install -r requirements_prod.txt
        echo "✓ Dépendances installées"
        
        echo ""
        echo "=== INSTALLATION TERMINÉE ==="
        echo "Packages installés:"
        pip list
    else
        echo "⚠️  Fichier requirements_prod.txt non trouvé"
    fi
fi

echo ""
echo "Script terminé avec succès! 🎉" 