from flask import Blueprint, request

from app.api.erreurs import reponse_erreur
from app.api.parametres import (
    lire_date_heure_requete,
)
from app.conteneur import (
    obtenir_services_application,
)


poteaux_api = Blueprint(
    "poteaux_api",
    __name__,
)

@poteaux_api.get("/poteaux/<int:poteau_id>/evaluation")
def evaluer_poteau(poteau_id: int):

    date_heure, erreur = (
        lire_date_heure_requete()
    )

    if erreur is not None:
        return erreur

    service_poteaux = obtenir_services_application().poteaux

    resultat = service_poteaux.evaluer_poteau(
        poteau_id,
        date_heure,
    )

    if resultat is None:
        return reponse_erreur(
            code="POTEAU_INTROUVABLE",
            message=(
                "Aucun panneau n'est associé "
                "à ce poteau."
            ),
            statut=404,
        )

    return resultat, 200

@poteaux_api.get("/poteaux/proches")
def trouver_poteaux_proches():
    latitude = request.args.get(
        "latitude",
        type=float,
    )
    longitude = request.args.get(
        "longitude",
        type=float,
    )
    rayon = request.args.get(
        "rayon",
        default=300,
        type=int,
    )
    limite = request.args.get(
        "limite",
        default=20,
        type=int,
    )

    if latitude is None or longitude is None:
        return reponse_erreur(
            code="COORDONNEES_MANQUANTES",
            message=(
                "Les paramètres latitude et longitude "
                "sont obligatoires."
            ),
            statut=400,
        )

    if rayon is None or limite is None:
        return reponse_erreur(
            code="PARAMETRES_INVALIDES",
            message=(
                "Le rayon et la limite doivent être "
                "des nombres entiers."
            ),
            statut=422,
        )

    date_heure, erreur = (
        lire_date_heure_requete()
    )

    if erreur is not None:
        return erreur

    service_poteaux = obtenir_services_application().poteaux
    try:
        poteaux = service_poteaux.trouver_poteaux_proches(
            latitude=latitude,
            longitude=longitude,
            date_heure=date_heure,
            rayon_metres=rayon,
            limite=limite,
        )
    except ValueError as error:
        return reponse_erreur(
            code="RECHERCHE_INVALIDE",
            message=str(error),
            statut=422,
        )

    return {
        "centre": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "date_heure": date_heure.isoformat(),
        "rayon_metres": rayon,
        "nombre": len(poteaux),
        "poteaux": poteaux,
    }, 200