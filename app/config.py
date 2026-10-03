import os

from pathlib import Path


RACINE_PROJET = (
    Path(__file__).resolve().parent.parent
)

DOSSIER_DONNEES = RACINE_PROJET / "data"
CHEMIN_BASE_DONNEES = (
    DOSSIER_DONNEES / "parking.db"
)


class Configuration:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{CHEMIN_BASE_DONNEES}",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    API_PREFIXE = "/api/v1"
    FUSEAU_HORAIRE = "America/Toronto"

    TESTING = False
    DEBUG = (
        os.getenv("FLASK_DEBUG", "0") == "1"
    )