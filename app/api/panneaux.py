from flask import Blueprint, request

from app.api.erreurs import reponse_erreur
from app.api.parametres import (
    lire_date_heure_requete,
)
from app.conteneur import (
    obtenir_services_application,
)


panneaux_api = Blueprint(
    "panneaux_api",
    __name__,
)

@panneaux_api.get("/panneaux/<int:identifiant>")
def obtenir_panneau(identifiant: int):
    panneau = (
        obtenir_services_application()
        .panneaux
        .obtenir(identifiant)
    )

    if panneau is None:
        return reponse_erreur(
            code="PANNEAU_INTROUVABLE",
            message="Le panneau demandé n’existe pas.",
            statut=404,
        )

    return panneau.vers_dictionnaire(), 200

@panneaux_api.get("/panneaux")
def lister_panneaux():
    arrondissement = request.args.get(
        "arrondissement"
    )
    limite = request.args.get(
        "limite",
        default=20,
        type=int,
    )

    if limite is None:
        return reponse_erreur(
            code="LIMITE_INVALIDE",
            message="La limite doit être un nombre entier.",
            statut=422,
        )

    try:
        panneaux = (
            obtenir_services_application()
            .panneaux
            .lister(
                arrondissement=arrondissement,
                limite=limite,
            )
        )
    except ValueError as error:
        return reponse_erreur(
            code="LIMITE_INVALIDE",
            message=str(error),
            statut=422,
        )

    return {
        "nombre": len(panneaux),
        "panneaux": [
            panneau.vers_dictionnaire()
            for panneau in panneaux
        ],
    }, 200

@panneaux_api.get("/panneaux/proches")
def trouver_panneaux_proches():
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
            code="PARAMETRES_MANQUANTS",
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

    try:
        panneaux = (
            obtenir_services_application()
            .panneaux
            .trouver_proches(
                latitude=latitude,
                longitude=longitude,
                rayon_metres=rayon,
                limite=limite,
            )
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
        "rayon_metres": rayon,
        "nombre": len(panneaux),
        "panneaux": panneaux,
    }, 200

@panneaux_api.get("/panneaux/<int:identifiant>/interpretation")
def interpreter_panneau(identifiant: int) -> dict | None:
    interpretation = (
        obtenir_services_application()
        .panneaux
        .obtenir_interpretation(identifiant)
    )

    if interpretation is None:
        return reponse_erreur(
            code="PANNEAU_INTROUVABLE",
            message=(
                "Le panneau demandé "
                "n'existe pas."
            ),
            statut=404,
        )

    return interpretation, 200

@panneaux_api.get("/panneaux/<int:identifiant>/evaluation")
def evaluer_panneau(identifiant: int):
    date_heure, erreur = (
        lire_date_heure_requete()
    )

    if erreur is not None:
        return erreur

    resultat = (
        obtenir_services_application()
        .panneaux
        .evaluer_panneau(
            identifiant,
            date_heure,
        )
    )

    if resultat is None:
        return reponse_erreur(
            code="PANNEAU_INTROUVABLE",
            message=(
                "Le panneau demandé n'existe pas."
            ),
            statut=404,
        )

    return resultat, 200