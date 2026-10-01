from app.models import Panneau
from app.dao import PanneauDAO
from math import asin, cos, radians, sin, sqrt

RAYON_TERRE_METRES = 6_371_000

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

    #Formule de Haversine que je ne comprends pas
    @staticmethod
    def calculer_distance_metres(
            latitude_1: float,
            longitude_1: float,
            latitude_2: float,
            longitude_2: float,
    ) -> float:
        latitude_1_rad = radians(latitude_1)
        latitude_2_rad = radians(latitude_2)

        difference_latitude = radians(
            latitude_2 - latitude_1
        )
        difference_longitude = radians(
            longitude_2 - longitude_1
        )

        valeur = (
                sin(difference_latitude / 2) ** 2
                + cos(latitude_1_rad)
                * cos(latitude_2_rad)
                * sin(difference_longitude / 2) ** 2
        )

        angle = 2 * asin(sqrt(valeur))

        return RAYON_TERRE_METRES * angle

    #Pour eviter de calculer la distance avec chaque panneau de la base de donner
    #Creation d'une "boite" qui va etre utiliser dans la formule d'Haversine
    @staticmethod
    def calculer_limites_recherche(
            latitude: float,
            longitude: float,
            rayon_metres: int,
    ) -> tuple[float, float, float, float]:
        variation_latitude = rayon_metres / 111_320

        variation_longitude = rayon_metres / (
                111_320 * cos(radians(latitude))
        )

        latitude_min = latitude - variation_latitude
        latitude_max = latitude + variation_latitude
        longitude_min = longitude - variation_longitude
        longitude_max = longitude + variation_longitude

        return (
            latitude_min,
            latitude_max,
            longitude_min,
            longitude_max,
        )

    @staticmethod
    def creer_resultat_proximite(
            panneau: Panneau,
            distance_metres: float,
    ) -> dict:
        resultat = panneau.vers_dictionnaire()
        resultat["distance_metres"] = round(
            distance_metres,
            1,
        )

        return resultat

    def trouver_proches(
            self,
            latitude: float,
            longitude: float,
            rayon_metres: int = 300,
            limite: int = 20,
    ) -> list[dict]:
        self._valider_recherche(
            latitude,
            longitude,
            rayon_metres,
            limite,
        )

        (
            latitude_min,
            latitude_max,
            longitude_min,
            longitude_max,
        ) = self.calculer_limites_recherche(
            latitude,
            longitude,
            rayon_metres,
        )

        candidats = self.dao.trouver_dans_zone(
            latitude_min=latitude_min,
            latitude_max=latitude_max,
            longitude_min=longitude_min,
            longitude_max=longitude_max,
        )

        resultats = []

        for panneau in candidats:
            distance = self.calculer_distance_metres(
                latitude,
                longitude,
                panneau.latitude,
                panneau.longitude,
            )

            if distance <= rayon_metres:
                resultats.append(
                    self.creer_resultat_proximite(
                        panneau,
                        distance,
                    )
                )

        resultats.sort(
            key=lambda panneau: panneau["distance_metres"]
        )

        return resultats[:limite]

    def _valider_recherche(
            self,
            latitude: float,
            longitude: float,
            rayon_metres: int,
            limite: int,
    ) -> None:
        if not -90 <= latitude <= 90:
            raise ValueError(
                "La latitude doit être comprise entre -90 et 90."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "La longitude doit être comprise entre -180 et 180."
            )

        if rayon_metres <= 0:
            raise ValueError(
                "Le rayon doit être supérieur à zéro."
            )

        if rayon_metres > 5_000:
            raise ValueError(
                "Le rayon maximal est de 5 000 mètres."
            )

        if limite <= 0 or limite > 100:
            raise ValueError(
                "La limite doit être comprise entre 1 et 100."
            )