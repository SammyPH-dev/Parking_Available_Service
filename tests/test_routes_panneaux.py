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

def test_evaluation_sans_date_utilise_heure_actuelle(
    client,
    application,
):
    with application.app_context():
        panneau = Panneau(
            poteau_id=700,
            code="AD-TT",
            description=r"\A EN TOUT TEMPS",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        db.session.add(panneau)
        db.session.commit()

        identifiant = panneau.id

    reponse = client.get(
        f"/api/panneaux/{identifiant}/evaluation"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert (
        contenu["evaluation_temporelle"]
        ["regle_active"]
        is True
    )


def test_evaluation_date_heure_invalide(client):
    reponse = client.get(
        "/api/panneaux/67/evaluation"
        "?date_heure=incorrect"
    )

    assert reponse.status_code == 422

    contenu = reponse.get_json()

    assert (
        contenu["erreur"]["code"]
        == "DATE_HEURE_INVALIDE"
    )


def test_evaluation_panneau_introuvable(client):
    reponse = client.get(
        "/api/panneaux/999999/evaluation"
        "?date_heure=2026-10-07T14:00:00"
    )

    assert reponse.status_code == 404

    contenu = reponse.get_json()

    assert (
        contenu["erreur"]["code"]
        == "PANNEAU_INTROUVABLE"
    )

def test_evaluation_panneau_en_tout_temps(
    client,
    application,
):
    with application.app_context():
        panneau = Panneau(
            poteau_id=100,
            code="AD-TT",
            description=r"\A EN TOUT TEMPS",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        db.session.add(panneau)
        db.session.commit()

        identifiant = panneau.id

    reponse = client.get(
        f"/api/panneaux/{identifiant}/evaluation"
        "?date_heure=2026-10-07T14:00:00"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert contenu["type_regle"] == "ARRET_INTERDIT"
    assert contenu["interpretation_complete"] is True

    evaluation = contenu["evaluation_temporelle"]

    assert evaluation["en_tout_temps"] is True
    assert evaluation["regle_active"] is True
    assert evaluation["analyse_complete"] is True

    assert contenu["statut"]["code"] == "ARRET_INTERDIT"

    assert (
            contenu["statut"][
                "stationnement_autorise_selon_ce_panneau"
            ]
            is False
    )
def test_evaluation_poteau_introuvable(client):
    reponse = client.get(
        "/api/poteaux/999999/evaluation"
        "?date_heure=2026-10-07T09:00:00"
    )

    assert reponse.status_code == 404

    contenu = reponse.get_json()

    assert (
        contenu["erreur"]["code"]
        == "POTEAU_INTROUVABLE"
    )


def test_evaluation_poteau_priorise_interdiction(
    client,
    application,
):
    with application.app_context():
        panneau_interdit = Panneau(
            poteau_id=500,
            code="P-TT",
            description=r"\P EN TOUT TEMPS",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        panneau_limite = Panneau(
            poteau_id=500,
            code="P-60",
            description="P 60 min 08h-18h",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        db.session.add_all([
            panneau_interdit,
            panneau_limite,
        ])
        db.session.commit()

    reponse = client.get(
        "/api/poteaux/500/evaluation"
        "?date_heure=2026-10-07T09:00:00"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert contenu["poteau_id"] == 500
    assert contenu["nombre_panneaux"] == 2

    assert (
        contenu["statut_global"]["code"]
        == "STATIONNEMENT_INTERDIT"
    )

    assert (
        contenu["statut_global"][
            "stationnement_autorise_selon_ce_poteau"
        ]
        is False
    )

def test_recherche_poteaux_proches_evalues(
    client,
    application,
):
    with application.app_context():
        panneaux = [
            Panneau(
                poteau_id=100,
                code="P-TT",
                description=r"\P EN TOUT TEMPS",
                arrondissement="Test",
                latitude=45.5019,
                longitude=-73.5674,
            ),
            Panneau(
                poteau_id=100,
                code="P-60",
                description="P 60 min 08h-18h",
                arrondissement="Test",
                latitude=45.5019,
                longitude=-73.5674,
            ),
        ]

        db.session.add_all(panneaux)
        db.session.commit()

    reponse = client.get(
        "/api/poteaux/proches"
        "?latitude=45.5019"
        "&longitude=-73.5674"
        "&date_heure=2026-10-07T09:00:00"
        "&rayon=300"
        "&limite=10"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert contenu["nombre"] == 1
    assert len(contenu["poteaux"]) == 1

    poteau = contenu["poteaux"][0]

    assert poteau["poteau_id"] == 100
    assert poteau["nombre_panneaux"] == 2
    assert poteau["distance_metres"] == 0

    assert (
        poteau["statut_global"]["code"]
        == "STATIONNEMENT_INTERDIT"
    )

def test_date_utc_convertie_vers_montreal(
    client,
    application,
):
    with application.app_context():
        panneau = Panneau(
            poteau_id=701,
            code="AD-TT",
            description=r"\A EN TOUT TEMPS",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        db.session.add(panneau)
        db.session.commit()

    reponse = client.get(
        "/api/poteaux/proches"
        "?latitude=45.5"
        "&longitude=-73.5"
        "&date_heure=2026-10-07T18:00:00Z"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert (
        contenu["date_heure"]
        == "2026-10-07T14:00:00-04:00"
    )

def test_recherche_poteaux_coordonnees_obligatoires(
    client,
):
    reponse = client.get(
        "/api/poteaux/proches"
        "?date_heure=2026-10-07T09:00:00"
    )

    assert reponse.status_code == 400

    contenu = reponse.get_json()

    assert (
        contenu["erreur"]["code"]
        == "COORDONNEES_MANQUANTES"
    )

def test_poteaux_proches_sans_date_utilise_heure_actuelle(
    client,
):
    reponse = client.get(
        "/api/poteaux/proches"
        "?latitude=45.5"
        "&longitude=-73.5"
    )

    assert reponse.status_code == 200

    contenu = reponse.get_json()

    assert contenu["date_heure"] is not None