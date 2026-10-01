from app.extensions import db
from app.models import Panneau


def test_sante(client):
    reponse = client.get(
        "/api/sante"
    )

    assert reponse.status_code == 200


def test_coordonnees_obligatoires(client):
    reponse = client.get(
        "/api/panneaux/proches"
    )

    assert reponse.status_code == 400

    contenu = reponse.get_json()

    assert (
        contenu["erreur"]["code"]
        == "PARAMETRES_MANQUANTS"
    )


def test_latitude_invalide(client):
    reponse = client.get(
        "/api/panneaux/proches"
        "?latitude=100"
        "&longitude=-73.5674"
    )

    assert reponse.status_code == 422


def test_recherche_panneau_proche(
    client,
    application,
):
    with application.app_context():
        panneau_proche = Panneau(
            id=1,
            poteau_id=100,
            code="TEST-PROCHE",
            description="Panneau proche",
            arrondissement="Ville-Marie",
            latitude=45.5019,
            longitude=-73.5674,
        )

        panneau_eloigne = Panneau(
            id=2,
            poteau_id=200,
            code="TEST-ELOIGNE",
            description="Panneau éloigné",
            arrondissement="Ville-Marie",
            latitude=45.5200,
            longitude=-73.5674,
        )

        db.session.add_all([
            panneau_proche,
            panneau_eloigne,
        ])
        db.session.commit()

    reponse = client.get(
        "/api/panneaux/proches"
        "?latitude=45.5019"
        "&longitude=-73.5674"
        "&rayon=100"
        "&limite=10"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert contenu["nombre"] == 1
    assert len(contenu["panneaux"]) == 1

    resultat = contenu["panneaux"][0]

    assert resultat["id"] == 1
    assert resultat["distance_metres"] == 0