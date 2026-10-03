from datetime import datetime
from app.services import ServicePanneaux
from app.dao import PanneauDAO
from app.extensions import db
from app.models import Panneau


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
