from flask import Flask

from app.api import enregistrer_api
from app.config import (
    Configuration,
    DOSSIER_DONNEES,
)
from app.extensions import db


def creer_application(
    configuration_test: dict | None = None,
) -> Flask:
    app = Flask(__name__)

    app.config.from_object(
        Configuration
    )

    if configuration_test is not None:
        app.config.update(
            configuration_test
        )

    DOSSIER_DONNEES.mkdir(
        parents=True,
        exist_ok=True,
    )

    db.init_app(app)

    from app.conteneur import (
        creer_services_application,
    )

    app.extensions[
        "services_application"
    ] = creer_services_application()

    enregistrer_api(
        app,
        prefixe=app.config["API_PREFIXE"],
    )

    with app.app_context():
        from app import models

        db.create_all()

    return app