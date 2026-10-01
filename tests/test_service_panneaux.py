from datetime import datetime, time, date
from app.services import ServicePanneaux
from app.dao import PanneauDAO
from app.extensions import db
from app.models import Panneau

def test_distance_coordonnees_identiques():
    distance = (
        ServicePanneaux
        .calculer_distance_metres(
            latitude_1=45.5019,
            longitude_1=-73.5674,
            latitude_2=45.5019,
            longitude_2=-73.5674,
        )
    )

    assert distance == 0


def test_distance_environ_cent_metres():
    distance = (
        ServicePanneaux
        .calculer_distance_metres(
            latitude_1=45.5019,
            longitude_1=-73.5674,
            latitude_2=45.5028,
            longitude_2=-73.5674,
        )
    )

    assert 95 <= distance <= 105


def creer_panneau_test(description: str) -> Panneau:
    return Panneau(
        id=1,
        poteau_id=100,
        code="TEST",
        description=description,
        arrondissement="Ville-Marie",
        latitude=45.5019,
        longitude=-73.5674,
    )

def test_interpreter_stationnement_interdit():
    panneau = creer_panneau_test(
        "\\P EN TOUT TEMPS"
    )

    resultat = (
        ServicePanneaux
        .interpreter_panneau(panneau)
    )

    assert (
        resultat["type_regle"]
        == "STATIONNEMENT_INTERDIT"
    )


def test_interpreter_arret_interdit():
    panneau = creer_panneau_test(
        "\\A EN TOUT TEMPS"
    )

    resultat = (
        ServicePanneaux
        .interpreter_panneau(panneau)
    )

    assert (
        resultat["type_regle"]
        == "ARRET_INTERDIT"
    )


def test_interpreter_stationnement_payant():
    panneau = creer_panneau_test(
        "STATIONNEMENT TARIFÉ"
    )

    resultat = (
        ServicePanneaux
        .interpreter_panneau(panneau)
    )

    assert (
        resultat["type_regle"]
        == "STATIONNEMENT_PAYANT"
    )


def test_interpreter_reglement_conditionnel():
    panneau = creer_panneau_test(
        "\\P 9h-23h EXCEPTE S3R"
    )

    resultat = (
        ServicePanneaux
        .interpreter_panneau(panneau)
    )

    assert (
        resultat["type_regle"]
        == "REGLEMENT_CONDITIONNEL"
    )

def test_extraire_heures_sans_minutes():
    plage = (
        ServicePanneaux
        .extraire_plage_horaire(
            "\\P 9h-23h EXCEPTE S3R"
        )
    )

    assert plage == (
        time(9, 0),
        time(23, 0),
    )


def test_extraire_heures_avec_minutes():
    plage = (
        ServicePanneaux
        .extraire_plage_horaire(
            (
                "\\P 12h30-15h30 "
                "MERCREDI"
            )
        )
    )

    assert plage == (
        time(12, 30),
        time(15, 30),
    )


def test_heure_dans_plage_normale():
    resultat = (
        ServicePanneaux
        .heure_dans_plage(
            heure_actuelle=time(14, 0),
            debut=time(12, 30),
            fin=time(15, 30),
        )
    )

    assert resultat is True


def test_heure_hors_plage_normale():
    resultat = (
        ServicePanneaux
        .heure_dans_plage(
            heure_actuelle=time(16, 0),
            debut=time(12, 30),
            fin=time(15, 30),
        )
    )

    assert resultat is False


def test_plage_traverse_minuit():
    assert (
        ServicePanneaux
        .heure_dans_plage(
            heure_actuelle=time(22, 0),
            debut=time(19, 0),
            fin=time(7, 0),
        )
        is True
    )

    assert (
        ServicePanneaux
        .heure_dans_plage(
            heure_actuelle=time(3, 0),
            debut=time(19, 0),
            fin=time(7, 0),
        )
        is True
    )

    assert (
        ServicePanneaux
        .heure_dans_plage(
            heure_actuelle=time(12, 0),
            debut=time(19, 0),
            fin=time(7, 0),
        )
        is False
    )


def test_evaluer_plage_horaire():
    resultat = (
        ServicePanneaux
        .evaluer_plage_horaire(
            description="\\P 9h-23h",
            date_heure=datetime(
                2026,
                10,
                1,
                14,
                30,
            ),
        )
    )

    assert (
        resultat["plage_horaire_trouvee"]
        is True
    )
    assert resultat["debut"] == "09:00"
    assert resultat["fin"] == "23:00"
    assert (
        resultat["heure_dans_plage"]
        is True
    )

def test_extraire_un_jour():
    jours = (
        ServicePanneaux
        .extraire_jours_semaine(
            (
                "\\P 12h30-15h30 "
                "MERCREDI"
            )
        )
    )

    assert jours == {2}

def test_extraire_lundi_au_vendredi():
    jours = (
        ServicePanneaux
        .extraire_jours_semaine(
            (
                "\\A 06h-09h30 "
                "LUN. AU VEN."
            )
        )
    )

    assert jours == {
        0,
        1,
        2,
        3,
        4,
    }

def test_extraire_lundi_au_samedi():
    jours = (
        ServicePanneaux
        .extraire_jours_semaine(
            "\\P 8h-19h LUN A SAM"
        )
    )

    assert jours == {
        0,
        1,
        2,
        3,
        4,
        5,
    }

def test_extraire_plusieurs_jours():
    jours = (
        ServicePanneaux
        .extraire_jours_semaine(
            (
                "\\P 9h-17h "
                "LUNDI MERCREDI JEUDI"
            )
        )
    )

    assert jours == {0, 2, 3}


def test_jour_correspond():
    resultat = (
        ServicePanneaux
        .evaluer_jour_semaine(
            description=(
                "\\P 9h-17h LUN A VEN"
            ),
            date_heure=datetime(
                2026,
                10,
                5,
                10,
                0,
            ),
        )
    )

    assert resultat["jours_trouves"] is True

    assert (
        resultat["jour_correspond"]
        is True
    )

def test_jour_ne_correspond_pas():
    resultat = (
        ServicePanneaux
        .evaluer_jour_semaine(
            description=(
                "\\P 9h-17h LUN A VEN"
            ),
            date_heure=datetime(
                2026,
                10,
                10,
                10,
                0,
            ),
        )
    )

    assert (
        resultat["jour_correspond"]
        is False
    )

def test_aucun_jour_dans_description():
    resultat = (
        ServicePanneaux
        .evaluer_jour_semaine(
            description="\\P 9h-23h",
            date_heure=datetime(
                2026,
                10,
                5,
                10,
                0,
            ),
        )
    )

    assert (
        resultat["jours_trouves"]
        is False
    )
    assert (
        resultat["jour_correspond"]
        is None
    )

def test_extraire_periode_saisonniere():
    periode = (
        ServicePanneaux
        .extraire_periode_saisonniere(
            (
                "\\P 12h30-15h30 "
                "MERCREDI "
                "1 AVRIL AU 1 DEC"
            )
        )
    )

    assert periode == (
        (4, 1),
        (12, 1),
    )

def test_extraire_periode_sans_espaces():
    periode = (
        ServicePanneaux
        .extraire_periode_saisonniere(
            (
                "\\P 12h30-15h30 "
                "MARDI "
                "1AVRIL AU 1DEC"
            )
        )
    )

    assert periode == (
        (4, 1),
        (12, 1),
    )

def test_date_dans_periode():
    resultat = (
        ServicePanneaux
        .date_dans_periode(
            date_actuelle=date(
                2026,
                10,
                1,
            ),
            debut=(4, 1),
            fin=(12, 1),
        )
    )

    assert resultat is True

def test_date_hors_periode():
    resultat = (
        ServicePanneaux
        .date_dans_periode(
            date_actuelle=date(
                2026,
                2,
                1,
            ),
            debut=(4, 1),
            fin=(12, 1),
        )
    )

    assert resultat is False

def test_periode_traverse_nouvel_an():
    assert (
        ServicePanneaux
        .date_dans_periode(
            date_actuelle=date(
                2026,
                12,
                15,
            ),
            debut=(11, 1),
            fin=(3, 31),
        )
        is True
    )

    assert (
        ServicePanneaux
        .date_dans_periode(
            date_actuelle=date(
                2026,
                2,
                15,
            ),
            debut=(11, 1),
            fin=(3, 31),
        )
        is True
    )

    assert (
        ServicePanneaux
        .date_dans_periode(
            date_actuelle=date(
                2026,
                7,
                15,
            ),
            debut=(11, 1),
            fin=(3, 31),
        )
        is False
    )

def test_evaluer_periode_saisonniere():
    resultat = (
        ServicePanneaux
        .evaluer_periode_saisonniere(
            description=(
                "\\P 12h30-15h30 "
                "MERCREDI "
                "1 AVRIL AU 1 DEC"
            ),
            date_heure=datetime(
                2026,
                10,
                7,
                14,
                0,
            ),
        )
    )

    assert (
        resultat["periode_trouvee"]
        is True
    )
    assert (
        resultat["date_dans_periode"]
        is True
    )

def test_regle_temporelle_toutes_conditions_valides():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 10, 7, 14, 0)

    resultat = ServicePanneaux.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is True
    assert resultat["analyse_complete"] is True


def test_regle_temporelle_hors_horaire():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 10, 7, 16, 0)

    resultat = ServicePanneaux.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is False


def test_regle_temporelle_mauvais_jour():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 10, 8, 14, 0)

    resultat = ServicePanneaux.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is False


def test_regle_temporelle_hors_periode():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 1, 7, 14, 0)

    resultat = ServicePanneaux.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is False


def test_regle_temporelle_condition_non_reconnue():
    description = r"\P 9h-23h EXCEPTE S3R"
    date_heure = datetime(2026, 10, 7, 14, 0)

    resultat = ServicePanneaux.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is True
    assert resultat["analyse_complete"] is False
    assert "EXCEPTE" in resultat["expressions_non_supportees"]


def test_regle_temporelle_sans_condition_temporelle():
    resultat = ServicePanneaux.evaluer_regle_temporelle(
        "STATIONNEMENT TARIFÉ",
        datetime(2026, 10, 7, 14, 0),
    )

    assert resultat["regle_active"] is None

def test_regle_en_tout_temps_est_active():
    resultat = ServicePanneaux.evaluer_regle_temporelle(
        r"\A EN TOUT TEMPS",
        datetime(2026, 10, 7, 14, 0),
    )

    assert resultat["regle_active"] is True
    assert resultat["en_tout_temps"] is True
    assert resultat["analyse_complete"] is True

def test_statut_arret_interdit():
    interpretation = {
        "type_regle": "ARRET_INTERDIT",
        "panneau": {
            "description": r"\A EN TOUT TEMPS"
        },
    }

    evaluation = {
        "analyse_complete": True,
        "regle_active": True,
    }

    resultat = ServicePanneaux.determiner_statut(
        interpretation,
        evaluation,
    )

    assert resultat["code"] == "ARRET_INTERDIT"
    assert (
        resultat[
            "stationnement_autorise_selon_ce_panneau"
        ]
        is False
    )



    #----------
def test_statut_regle_inactive():
    interpretation = {
        "type_regle": "REGLEMENT_CONDITIONNEL",
        "panneau": {
            "description": r"\P 8h-10h"
        },
    }

    evaluation = {
        "analyse_complete": True,
        "regle_active": False,
        }

    resultat = ServicePanneaux.determiner_statut(
        interpretation,
        evaluation,
    )

    assert resultat["code"] == "REGLE_INACTIVE"
    assert (
            resultat[
                "stationnement_autorise_selon_ce_panneau"
            ]
            is None
    )

def test_statut_condition_non_supportee():
    interpretation = {
        "type_regle": "REGLEMENT_CONDITIONNEL",
        "panneau": {
            "description": r"\P 9h-23h EXCEPTE S3R"
        },
    }

    evaluation = {
        "analyse_complete": False,
        "regle_active": True,
    }

    resultat = ServicePanneaux.determiner_statut(
        interpretation,
        evaluation,
    )

    assert resultat["code"] == "INDETERMINE"

def test_statut_stationnement_interdit_conditionnel():
    interpretation = {
        "type_regle": "REGLEMENT_CONDITIONNEL",
        "panneau": {
            "description": r"\P 8h-10h"
        },
    }

    evaluation = {
        "analyse_complete": True,
        "regle_active": True,
    }

    resultat = ServicePanneaux.determiner_statut(
        interpretation,
        evaluation,
    )

    assert (
            resultat["code"]
            == "STATIONNEMENT_INTERDIT"
    )
    assert (
            resultat[
                "stationnement_autorise_selon_ce_panneau"
            ]
            is False
    )

def test_statut_stationnement_limite():
    interpretation = {
        "type_regle": "STATIONNEMENT_LIMITE",
        "panneau": {
            "description": "P 60 min 08h-18h"
        },
    }

    evaluation = {
        "analyse_complete": True,
        "regle_active": True,
    }

    resultat = ServicePanneaux.determiner_statut(
        interpretation,
        evaluation,
    )

    assert (
            resultat["code"]
            == "STATIONNEMENT_LIMITE"
    )
    assert (
            resultat[
                "stationnement_autorise_selon_ce_panneau"
            ]
            is True
    )



def test_statut_poteau_priorise_interdiction():
    evaluations = [
        {
            "statut": {
                "code": "STATIONNEMENT_LIMITE"
            }
        },
        {
            "statut": {
                "code": "STATIONNEMENT_INTERDIT"
            }
        },
    ]

    resultat = (
        ServicePanneaux.determiner_statut_poteau(
            evaluations
        )
    )

    assert (
        resultat["code"]
        == "STATIONNEMENT_INTERDIT"
    )
    assert (
        resultat[
            "stationnement_autorise_selon_ce_poteau"
        ]
        is False
    )

def test_aux_autobus_est_non_supporte():
    description = r"\P AUX AUTOBUS"

    evaluation = (
        ServicePanneaux.evaluer_regle_temporelle(
            description,
            datetime(2026, 10, 7, 14, 0),
        )
    )

    assert evaluation["analyse_complete"] is False
    assert evaluation["regle_active"] is None

    assert (
        "AUX AUTOBUS"
        in evaluation["expressions_non_supportees"]
    )

def test_trouver_poteaux_proches_regroupe_panneaux(
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
            Panneau(
                poteau_id=200,
                code="AD-TT",
                description=r"\A EN TOUT TEMPS",
                arrondissement="Test",
                latitude=45.5029,
                longitude=-73.5674,
            ),
        ]

        db.session.add_all(panneaux)
        db.session.commit()

        service = ServicePanneaux(
            PanneauDAO()
        )

        resultats = (
            service.trouver_poteaux_proches(
                latitude=45.5019,
                longitude=-73.5674,
                date_heure=datetime(
                    2026,
                    10,
                    7,
                    9,
                    0,
                ),
                rayon_metres=500,
                limite=10,
            )
        )

        assert len(resultats) == 2

        premier = resultats[0]

        assert premier["poteau_id"] == 100
        assert premier["nombre_panneaux"] == 2
        assert premier["distance_metres"] == 0

        assert (
            premier["statut_global"]["code"]
            == "STATIONNEMENT_INTERDIT"
        )