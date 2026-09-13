from pathlib import Path

from flask import Flask

from app.extensions import db


def creer_application() -> Flask:
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

    db.init_app(app)

    from app.routes import api

    app.register_blueprint(
        api,
        url_prefix="/api",
    )

    with app.app_context():
        from app import models

        db.create_all()

    return app