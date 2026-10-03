from datetime import datetime

from app.dao import PanneauDAO
from app.extensions import db
from app.models import Panneau
from app.services import (
    ServicePanneaux,
    ServicePoteaux,
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
        ServicePoteaux.determiner_statut_poteau(
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

        dao = PanneauDAO()

        service_panneaux = ServicePanneaux(
            dao
        )

        service_poteaux = ServicePoteaux(
            dao=dao,
            service_panneaux=service_panneaux,
        )

        resultats = (
            service_poteaux.trouver_poteaux_proches(
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