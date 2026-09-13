from sqlalchemy import func, select

from app.extensions import db
from app.models import Panneau


class PanneauDAO:

    #Obtenir un panneau a partir du ID
    def obtenir_par_id(self, identifiant: int) -> Panneau | None:
        return db.session.get(Panneau, identifiant)

    #Lister par arrondissement (optionnel) et avec une limite (defaut 20 panneaux)
    def lister(self, arrondissement: str | None = None, limite: int = 20) -> list[Panneau]:
        requete = select(Panneau)

        if arrondissement:
            requete = requete.where(func.lower(Panneau.arrondissement) == arrondissement.lower())

        requete = requete.order_by(Panneau.id).limit(limite)

        return list(db.session.scalars(requete))

    #Ajouter un panneau
    def ajouter(self, panneau: Panneau) -> None:
        db.session.add(panneau)

    #Supprimer un panneau
    def supprimer(self, panneau: Panneau) -> None:
        db.session.delete(panneau)