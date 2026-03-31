# ============================================================================
# shell.nix - D-SIG Stress Test Environment (NixOS 25.11)
# ============================================================================
# OBJECTIF: Environnement reproductible pour le stress test D-SIG v0.3
# PROJET: https://github.com/dravitch/dsig-standard/dsig-stress-test
# DATE: 2026-03-30
# DEPENDANCES PRINCIPALES:
#   - pandas, numpy (analyse de données)
#   - anthropic (LLM Claude)
#   - kaggle (téléchargement datasets)
#   - requests, aiohttp (appels HTTP)
#   - python-dateutil (gestion dates)
# ============================================================================

{ pkgs ? import <nixpkgs> {} }:

let
  # Version fixe de Python (3.12 recommandée)
  python = pkgs.python312;

  # Environnement Python avec les paquets Nix disponibles
  pythonEnv = python.withPackages (ps: with ps; [
    # ------------------------------------------------------------
    # DATA SCIENCE CORE
    # ------------------------------------------------------------
    numpy              # calculs numériques
    pandas             # manipulation données
    scipy              # calculs scientifiques
    scikit-learn       # utilitaires ML (utile pour l'analyse)

    # ------------------------------------------------------------
    # HTTP & API
    # ------------------------------------------------------------
    requests           # client HTTP
    aiohttp            # async HTTP
    websockets         # WebSocket (si besoin)
    urllib3            # HTTP robuste

    # ------------------------------------------------------------
    # CONFIGURATION & UTILITAIRES
    # ------------------------------------------------------------
    pyyaml             # fichiers YAML (config)
    python-dotenv      # variables d'environnement
    pydantic           # validation de données
    python-dateutil    # manipulation dates
    pytz               # fuseaux horaires
    colorama           # sortie colorée
    tqdm               # barres de progression

    # ------------------------------------------------------------
    # VISUALISATION (optionnel mais utile pour l'analyse)
    # ------------------------------------------------------------
    matplotlib
    seaborn
    plotly

    # ------------------------------------------------------------
    # OUTILS DE DÉVELOPPEMENT
    # ------------------------------------------------------------
    ipython            # shell interactif
    black              # formateur code
    isort              # tri imports
    flake8             # linter
    ruff               # linter rapide
    mypy               # type checking
    pytest             # framework de test
    pytest-cov         # couverture de code
    pytest-asyncio     # tests asynchrones

    # ------------------------------------------------------------
    # PACKAGES SYSTÈME (pip sera utilisé pour les dépendances non Nix)
    # ------------------------------------------------------------
    pip
    setuptools
    wheel
    virtualenv
  ]);

in
pkgs.mkShell {
  # ============================================================
  # PACKAGES SYSTÈME (outils CLI et libs C)
  # ============================================================
  buildInputs = [
    pythonEnv

    # Outils de développement
    pkgs.git
    pkgs.just              # task runner (recommandé)
    pkgs.direnv            # auto‑activation de l’environnement
    pkgs.ripgrep           # recherche rapide
    pkgs.fd                # alternative moderne à find
    pkgs.fzf               # recherche floue

    # Bibliothèques C (pour certains paquets Python)
    pkgs.gcc
    pkgs.pkg-config
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.openssl
    pkgs.libffi
    pkgs.libxml2           # nécessaire pour certains paquets (ex: lxml)

    # Pré-commit hooks (optionnel)
    pkgs.pre-commit
  ];

  # ============================================================
  # SHELL HOOK - CONFIGURATION AUTOMATIQUE
  # ============================================================
  shellHook = ''
    echo "============================================================"
    echo "🚀 D-SIG Stress Test Environment (v0.3)"
    echo "   Date: 2026-03-30"
    echo "   Python: $(python --version)"
    echo "============================================================"
    echo ""

    # ------------------------------------------------------------
    # Variables d'environnement pour les bibliothèques C
    # ------------------------------------------------------------
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.openssl.out}/lib:${pkgs.libxml2}/lib:''${LD_LIBRARY_PATH:-}"
    export PKG_CONFIG_PATH="${pkgs.openssl.dev}/lib/pkgconfig:${pkgs.zlib}/lib/pkgconfig:''${PKG_CONFIG_PATH:-}"

    # ------------------------------------------------------------
    # Virtual environment (avec site‑packages pour utiliser les paquets Nix)
    # ------------------------------------------------------------
    VENV_DIR=".venv"

    # Vérifier les permissions d’écriture
    if [ ! -w "." ]; then
      echo "❌ ERREUR: Répertoire non accessible en écriture"
      echo "   Veuillez vous déplacer dans un répertoire utilisateur."
      return 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
      echo "📦 Création du virtual environment..."
      python -m venv "$VENV_DIR" --system-site-packages --without-pip

      # Installer pip dans le venv (évite les problèmes de read‑only)
      echo "   Installation de pip dans le venv..."
      "$VENV_DIR/bin/python" -m ensurepip --default-pip
      "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
      echo "✅ Virtual environment créé"
    fi

    # Activer le venv
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activé: $VENV_DIR"
    echo ""

    # ------------------------------------------------------------
    # Installation des paquets Python non présents dans Nixpkgs
    # ------------------------------------------------------------
    echo "📥 Installation des paquets additionnels (pip)..."

    # Mise à jour de pip
    pip install --upgrade pip setuptools wheel --quiet 2>/dev/null || true

    # Paquets critiques pour le stress test
    echo "   • anthropic (client Claude)..."
    pip install --quiet anthropic 2>/dev/null || echo "⚠️  Échec installation anthropic"

    echo "   • kaggle (téléchargement datasets)..."
    pip install --quiet kaggle 2>/dev/null || echo "⚠️  Échec installation kaggle"

    echo "   • openmetrics (facultatif, pour OTel)..."
    pip install --quiet openmetrics 2>/dev/null || true

    # Autres paquets utiles
    pip install --quiet loguru cryptography sqlalchemy pandas-gbq 2>/dev/null || true

    echo "✅ Paquets additionnels installés"
    echo ""

    # ------------------------------------------------------------
    # Vérification de l’environnement Kaggle (si nécessaire)
    # ------------------------------------------------------------
    if [ -f "$HOME/.kaggle/kaggle.json" ]; then
      echo "🔑 Fichier kaggle.json trouvé."
    else
      echo "⚠️  Fichier kaggle.json non trouvé dans $HOME/.kaggle/"
      echo "   Pour télécharger les datasets, configurez vos identifiants Kaggle :"
      echo "   mkdir -p ~/.kaggle && cp /chemin/vers/kaggle.json ~/.kaggle/"
      echo "   chmod 600 ~/.kaggle/kaggle.json"
    fi

    # ------------------------------------------------------------
    # Variables d’environnement pour le projet
    # ------------------------------------------------------------
    export PYTHONPATH="''${PWD}:''${PWD}/src:''${PYTHONPATH:-}"
    export DSIG_ENV="development"
    export DSIG_DATA_PATH="''${PWD}/data"
    export DSIG_RESULTS_PATH="''${PWD}/results"
    export DSIG_LOGS_PATH="''${PWD}/logs"
    export PYTHON_KEYRING_BACKEND="keyring.backends.null.Keyring"
    export PYTHONDONTWRITEBYTECODE=1

    # Création des répertoires
    mkdir -p data results logs src/pipelines src/analysis src/utils config
    echo "✅ Répertoires créés"
    echo ""

    # ------------------------------------------------------------
    # Vérification des dépendances critiques
    # ------------------------------------------------------------
    echo "🔍 Vérification des dépendances:"

    check_package() {
      local pkg=$1
      local label=$2
      local critical=$3
      if python -c "import $pkg" 2>/dev/null; then
        local version=$(python -c "import $pkg; print(getattr($pkg, '__version__', 'OK'))" 2>/dev/null)
        echo "   ✅ $label: $version"
        return 0
      else
        if [ "$critical" = "true" ]; then
          echo "   ❌ $label - MANQUANT (CRITIQUE!)"
          return 1
        else
          echo "   ⚠️  $label - non installé (optionnel)"
          return 0
        fi
      fi
    }

    CRITICAL_OK=true
    check_package "pandas" "pandas" "true" || CRITICAL_OK=false
    check_package "numpy" "numpy" "true" || CRITICAL_OK=false
    check_package "anthropic" "anthropic" "true" || CRITICAL_OK=false
    check_package "kaggle" "kaggle" "false"  # pas critique, mais nécessaire pour les datasets
    check_package "yaml" "pyyaml" "true" || CRITICAL_OK=false
    echo ""

    if [ "$CRITICAL_OK" = "false" ]; then
      echo "❌ ERREUR: Dépendances critiques manquantes!"
      echo "   Exécutez: just install  (ou pip install -r requirements.txt)"
      echo ""
    fi

    # ------------------------------------------------------------
    # Informations finales
    # ------------------------------------------------------------
    echo "📊 Informations environnement:"
    echo "   Python: $(python --version)"
    echo "   Pip: $(pip --version | cut -d' ' -f1-2)"
    echo "   Location: $(pwd)"
    echo "   Venv: $VIRTUAL_ENV"
    echo ""

    echo "🔧 Commandes rapides (via justfile):"
    echo "   just setup         - Initialiser le projet"
    echo "   just install       - Installer dépendances (si besoin)"
    echo "   just test          - Lancer les tests"
    echo "   just format        - Formater le code"
    echo "   just lint          - Vérifier le code"
    echo "   just run           - Exécuter le stress test (Scenario 1)"
    echo ""
    echo "   # Exécution manuelle du stress test"
    echo "   python main.py"
    echo ""
    echo "   # Téléchargement du dataset Kaggle"
    echo "   kaggle datasets download -d freshersstaff/it-system-performance-and-resource-metrics -p data/ --unzip"
    echo ""
    echo "   # Vérification complète de l’environnement"
    echo "   python verify_environment.py"
    echo ""
    echo "✨ Environnement prêt pour le D-SIG Stress Test!"
    echo "============================================================"
    echo ""
  '';

  # Désactiver la génération de bytecode
  PYTHONDONTWRITEBYTECODE = "1";
}
