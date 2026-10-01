from flask import Blueprint, request

from app.dao import PanneauDAO
from app.services import ServicePanneaux


api = Blueprint("api", __name__)

service = ServicePanneaux(
    PanneauDAO()
)


def reponse_erreur(
    code: str,
    message: str,
    statut: int,
):
    return {
        "erreur": {
            "code": code,
            "message": message,
        }
    }, statut


@api.get("/sante")
def sante():
    return {
        "etat": "disponible",
        "service": "stationnement-montreal",
    }, 200


@api.get("/panneaux/<int:identifiant>")
def obtenir_panneau(identifiant: int):
    panneau = service.obtenir(identifiant)

    if panneau is None:
        return reponse_erreur(
            code="PANNEAU_INTROUVABLE",
            message="Le panneau demandé n’existe pas.",
            statut=404,
        )

    return panneau.vers_dictionnaire(), 200


@api.get("/panneaux")
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
        panneaux = service.lister(
            arrondissement=arrondissement,
            limite=limite,
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

@api.get("/panneaux/proches")
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
        panneaux = service.trouver_proches(
            latitude=latitude,
            longitude=longitude,
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
        "rayon_metres": rayon,
        "nombre": len(panneaux),
        "panneaux": panneaux,
    }, 200