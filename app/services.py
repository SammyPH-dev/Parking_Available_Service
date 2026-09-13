from app.models import Panneau
from app.dao import PanneauDAO


class ServicePanneaux:
    def __init__(self, dao: PanneauDAO) -> None:
        self.dao = dao

    def obtenir(self, identifiant: int) -> Panneau | None:
        return self.dao.obtenir_par_id(identifiant)

    def lister(self, arrondissement: str | None, limite: int) -> list[Panneau]:
        if limite <= 0:
            raise ValueError("La limite doit être supérieure à zéro.")

        if limite > 100:
            raise ValueError("La limite maximale est de 100.")

        return self.dao.lister(
            arrondissement=arrondissement,
            limite=limite,
        )