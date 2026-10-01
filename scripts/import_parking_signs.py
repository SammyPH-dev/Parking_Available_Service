import argparse
import json
import sys
from pathlib import Path
from typing import Any


RACINE_PROJET = (
    Path(__file__).resolve().parent.parent
)

if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(
        0,
        str(RACINE_PROJET),
    )


from app import creer_application
from app.extensions import db
from app.models import Panneau


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


def importer(limite: int | None= 500) -> tuple[int, int, int]:
    with CHEMIN_GEOJSON.open(
        encoding="utf-8"
    ) as fichier:
        donnees = json.load(fichier)

    application = creer_application()

    identifiants_importes = set()
    nombre_doublons = 0
    nombre_importe = 0
    nombre_ignore = 0

    with application.app_context():
        features = donnees["features"]

        if limite is not None:
            features = features[:limite]

        for feature in features:
            donnees_panneau = normaliser_feature(feature)
            identifiant = donnees_panneau["id"]

            if identifiant in identifiants_importes:
                nombre_doublons += 1

            identifiants_importes.add(
                identifiant
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

    return (
        len(identifiants_importes),
        nombre_ignore,
        nombre_doublons,
    )


def main() -> None:
    parseur = argparse.ArgumentParser(
        description=(
            "Importe les panneaux de stationnement "
            "dans la base de données."
        )
    )

    groupe = parseur.add_mutually_exclusive_group()

    groupe.add_argument(
        "--limite",
        type=int,
        default=500,
        help=(
            "Nombre maximal de features à importer. "
            "La valeur par défaut est 500."
        ),
    )

    groupe.add_argument(
        "--tout",
        action="store_true",
        help="Importe le fichier GeoJSON complet.",
    )

    arguments = parseur.parse_args()

    limite = (
        None
        if arguments.tout
        else arguments.limite
    )

    (
        nombre_unique,
        nombre_ignore,
        nombre_doublons,
    ) = importer(
        limite=limite
    )

    print(
        "Panneaux uniques importés ou mis à jour:",
        nombre_unique,
    )
    print(
        "Features dupliquées:",
        nombre_doublons,
    )
    print(
        "Features ignorées:",
        nombre_ignore,
    )


if __name__ == "__main__":
    main()