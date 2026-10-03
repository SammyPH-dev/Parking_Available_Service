def reponse_erreur(
    code: str,
    message: str,
    statut: int,
):
    return {
        "erreur": {
            "code": code,
            "message": message,
        }
    }, statut