from flask import Blueprint, request
from app.dao import PanneauDAO
from app.services import ServicePanneaux
from datetime import datetime
from zoneinfo import ZoneInfo


api = Blueprint("api", __name__)

service = ServicePanneaux(
    PanneauDAO()
)

FUSEAU_MONTREAL = ZoneInfo(
    "America/Toronto"
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

def lire_date_heure_requete():
    date_heure_texte = request.args.get(
        "date_heure"
    )

    if date_heure_texte is None:
        return (
            datetime.now(FUSEAU_MONTREAL),
            None,
        )

    # Accepte aussi le format UTC se terminant par Z.
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
        # Une date sans fuseau est considérée
        # comme une date de Montréal.
        date_heure = date_heure.replace(
            tzinfo=FUSEAU_MONTREAL
        )
    else:
        # Convertit une date UTC ou provenant
        # d'un autre fuseau vers Montréal.
        date_heure = date_heure.astimezone(
            FUSEAU_MONTREAL
        )

    return date_heure, None


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

@api.get("/panneaux/<int:identifiant>/interpretation")
def interpreter_panneau(identifiant: int) -> dict | None:
    interpretation = service.obtenir_interpretation(identifiant)

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

@api.get("/panneaux/<int:identifiant>/evaluation")
def evaluer_panneau(identifiant: int):
    date_heure, erreur = (
        lire_date_heure_requete()
    )

    if erreur is not None:
        return erreur

    resultat = service.evaluer_panneau(
        identifiant,
        date_heure,
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

@api.get("/poteaux/<int:poteau_id>/evaluation")
def evaluer_poteau(poteau_id: int):

    date_heure, erreur = (
        lire_date_heure_requete()
    )

    if erreur is not None:
        return erreur

    resultat = service.evaluer_poteau(
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

@api.get("/poteaux/proches")
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

    try:
        poteaux = service.trouver_poteaux_proches(
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

