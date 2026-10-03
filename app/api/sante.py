from flask import Blueprint

sante_api = Blueprint(
    "sante_api",
    __name__,
)


@sante_api.get("/sante")
def sante():
    return {
        "etat": "disponible",
        "service": "stationnement-montreal",
    }, 200