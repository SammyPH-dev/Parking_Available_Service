from pathlib import Path
from flask import Flask
from app.extensions import db
from app.routes import api

def creer_application(configuration_test: dict | None = None) -> Flask:
    app = Flask(__name__)

    racine_projet = Path(__file__).resolve().parent.parent
    chemin_bd = racine_projet / "data" / "parking.db"

    chemin_bd.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{chemin_bd}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    #test optionnel (Ca va creer une db de test)
    if configuration_test is not None:
        app.config.update(
            configuration_test
        )

    db.init_app(app)

    app.register_blueprint(
        api,
        url_prefix="/api",
    )

    with app.app_context():
        from app import models

        db.create_all()

    return app