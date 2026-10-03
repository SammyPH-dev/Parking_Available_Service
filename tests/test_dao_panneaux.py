from app.dao import PanneauDAO
from app.extensions import db
from app.models import Panneau


def test_lister_panneaux_par_poteau(application):
    with application.app_context():
        panneau_1 = Panneau(
            poteau_id=500,
            code="AD-TT",
            description=r"\A EN TOUT TEMPS",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        panneau_2 = Panneau(
            poteau_id=500,
            code="P-60",
            description="P 60 min 08h-18h",
            arrondissement="Test",
            latitude=45.5,
            longitude=-73.5,
        )

        autre_panneau = Panneau(
            poteau_id=600,
            code="P",
            description="PARCOMETRE",
            arrondissement="Test",
            latitude=45.6,
            longitude=-73.6,
        )

        db.session.add_all([
            panneau_1,
            panneau_2,
            autre_panneau,
        ])
        db.session.commit()

        dao = PanneauDAO()

        resultats = dao.lister_par_poteau(500)

        assert len(resultats) == 2
        assert all(
            panneau.poteau_id == 500
            for panneau in resultats
        )