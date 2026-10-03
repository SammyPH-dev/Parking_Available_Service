from flask import Flask

from app.api.panneaux import panneaux_api
from app.api.poteaux import poteaux_api
from app.api.sante import sante_api


def enregistrer_api(
    app: Flask,
    prefixe: str = "/api",
) -> None:
    app.register_blueprint(
        sante_api,
        url_prefix=prefixe,
    )
    app.register_blueprint(
        panneaux_api,
        url_prefix=prefixe,
    )
    app.register_blueprint(
        poteaux_api,
        url_prefix=prefixe,
    )


__all__ = [
    "enregistrer_api",
]