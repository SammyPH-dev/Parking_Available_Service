from datetime import datetime
from zoneinfo import ZoneInfo

from flask import request, current_app

from app.api.erreurs import reponse_erreur


def lire_date_heure_requete():
    fuseau_montreal = ZoneInfo(current_app.config["FUSEAU_HORAIRE"])
    date_heure_texte = request.args.get("date_heure")

    if date_heure_texte is None:
        return (
            datetime.now(fuseau_montreal),
            None,
        )

    if date_heure_texte.endswith("Z"):
        date_heure_texte = (
            date_heure_texte[:-1] + "+00:00"
        )

    try:
        date_heure = datetime.fromisoformat(
            date_heure_texte
        )
    except ValueError:
        erreur = reponse_erreur(
            code="DATE_HEURE_INVALIDE",
            message=(
                "La date et l'heure doivent respecter "
                "le format ISO, par exemple "
                "2026-10-07T14:00:00."
            ),
            statut=422,
        )

        return None, erreur

    if date_heure.tzinfo is None:
        date_heure = date_heure.replace(
            tzinfo=fuseau_montreal
        )
    else:
        date_heure = date_heure.astimezone(
            fuseau_montreal
        )

    return date_heure, None