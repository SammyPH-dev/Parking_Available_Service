from datetime import date, datetime, time

from app.domain.evaluation_temporelle import (
    EvaluateurTemporel,
)

def test_extraire_heures_sans_minutes():
    plage = (
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
        .heure_dans_plage(
            heure_actuelle=time(14, 0),
            debut=time(12, 30),
            fin=time(15, 30),
        )
    )

    assert resultat is True

def test_heure_hors_plage_normale():
    resultat = (
        EvaluateurTemporel
        .heure_dans_plage(
            heure_actuelle=time(16, 0),
            debut=time(12, 30),
            fin=time(15, 30),
        )
    )

    assert resultat is False


def test_plage_traverse_minuit():
    assert (
        EvaluateurTemporel
        .heure_dans_plage(
            heure_actuelle=time(22, 0),
            debut=time(19, 0),
            fin=time(7, 0),
        )
        is True
    )

    assert (
        EvaluateurTemporel
        .heure_dans_plage(
            heure_actuelle=time(3, 0),
            debut=time(19, 0),
            fin=time(7, 0),
        )
        is True
    )

    assert (
        EvaluateurTemporel
        .heure_dans_plage(
            heure_actuelle=time(12, 0),
            debut=time(19, 0),
            fin=time(7, 0),
        )
        is False
    )

def test_evaluer_plage_horaire():
    resultat = (
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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
        EvaluateurTemporel
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

    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is True
    assert resultat["analyse_complete"] is True


def test_regle_temporelle_hors_horaire():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 10, 7, 16, 0)

    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is False


def test_regle_temporelle_mauvais_jour():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 10, 8, 14, 0)

    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is False

def test_regle_temporelle_hors_periode():
    description = r"\P 12h30-15h30 MERCREDI 1 AVRIL AU 1 DEC"
    date_heure = datetime(2026, 1, 7, 14, 0)

    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is False


def test_regle_temporelle_condition_non_reconnue():
    description = r"\P 9h-23h EXCEPTE S3R"
    date_heure = datetime(2026, 10, 7, 14, 0)

    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        description,
        date_heure,
    )

    assert resultat["regle_active"] is True
    assert resultat["analyse_complete"] is False
    assert "EXCEPTE" in resultat["expressions_non_supportees"]


def test_regle_temporelle_sans_condition_temporelle():
    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        "STATIONNEMENT TARIFÉ",
        datetime(2026, 10, 7, 14, 0),
    )

    assert resultat["regle_active"] is None

def test_regle_en_tout_temps_est_active():
    resultat = EvaluateurTemporel.evaluer_regle_temporelle(
        r"\A EN TOUT TEMPS",
        datetime(2026, 10, 7, 14, 0),
    )

    assert resultat["regle_active"] is True
    assert resultat["en_tout_temps"] is True
    assert resultat["analyse_complete"] is True

def test_aux_autobus_est_non_supporte():
    description = r"\P AUX AUTOBUS"

    evaluation = (
        EvaluateurTemporel.evaluer_regle_temporelle(
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