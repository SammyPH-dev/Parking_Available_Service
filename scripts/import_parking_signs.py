import json
import sys
from pathlib import Path
from typing import Any
from app import creer_application
from app.extensions import db
from app.models import Panneau


RACINE_PROJET = Path(__file__).resolve().parent.parent

#Pour eviter le ModuleNotFoundError
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))


CHEMIN_GEOJSON = (
    RACINE_PROJET
    / "data"
    / "raw"
    / "parking_signs.geojson"
)


def normaliser_feature(
    feature: dict[str, Any],
) -> dict[str, Any] | None:
    proprietes = feature.get("properties") or {}
    geometrie = feature.get("geometry") or {}
    coordonnees = geometrie.get("coordinates") or []

    if len(coordonnees) < 2:
        return None

    longitude, latitude = coordonnees[:2]
    identifiant = proprietes.get("PANNEAU_ID_PAN")

    if (
        identifiant is None
        or latitude is None
        or longitude is None
    ):
        return None

    return {
        "id": int(identifiant),
        "poteau_id": proprietes.get("POTEAU_ID_POT"),
        "code": proprietes.get("CODE_RPA"),
        "description": (
            proprietes.get("DESCRIPTION_RPA")
            or ""
        ).strip(),
        "arrondissement": (
            proprietes.get("NOM_ARROND")
            or "Arrondissement inconnu"
        ),
        "latitude": float(latitude),
        "longitude": float(longitude),
    }


def importer(limite: int = 500) -> tuple[int, int]:
    with CHEMIN_GEOJSON.open(
        encoding="utf-8"
    ) as fichier:
        donnees = json.load(fichier)

    application = creer_application()

    nombre_importe = 0
    nombre_ignore = 0

    with application.app_context():
        for feature in donnees["features"][:limite]:
            donnees_panneau = normaliser_feature(
                feature
            )

            if donnees_panneau is None:
                nombre_ignore += 1
                continue

            panneau = db.session.get(
                Panneau,
                donnees_panneau["id"],
            )

            if panneau is None:
                panneau = Panneau(
                    **donnees_panneau
                )
                db.session.add(panneau)
            else:
                for attribut, valeur in (
                    donnees_panneau.items()
                ):
                    setattr(
                        panneau,
                        attribut,
                        valeur,
                    )

            nombre_importe += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return nombre_importe, nombre_ignore


def main() -> None:
    nombre_importe, nombre_ignore = importer()

    print("Panneaux importés:", nombre_importe)
    print("Panneaux ignorés:", nombre_ignore)


if __name__ == "__main__":
    main()