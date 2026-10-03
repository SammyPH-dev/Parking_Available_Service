from app.models import Panneau
from app.dao import PanneauDAO
from datetime import datetime
from app.domain.geographie import (
    calculer_distance_metres,
    calculer_limites_recherche,
    valider_recherche_geographique,
)
from app.domain.evaluation_temporelle import EvaluateurTemporel

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
        valider_recherche_geographique(
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
        ) = calculer_limites_recherche(
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
            distance = calculer_distance_metres(
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

    #permet de verifier si le type de panneau (ex: un 60 min seulement, un interdit de parker, etc)
    @staticmethod
    def interpreter_panneau(panneau: Panneau) -> dict:
        description = panneau.description.strip().upper()

        if (
                "PARCOMETRE" in description
                or "STATIONNEMENT TARIFÉ"
                in description
        ):
            type_regle = (
                "STATIONNEMENT_PAYANT"
            )
            explication = (
                "Le panneau indique une zone "
                "de stationnement payant."
            )

        elif description.startswith("\\A"):
            if "EN TOUT TEMPS" in description:
                type_regle = "ARRET_INTERDIT"
                explication = (
                    "L'arrêt est interdit "
                    "en tout temps."
                )
            else:
                type_regle = (
                    "REGLEMENT_CONDITIONNEL"
                )
                explication = (
                    "L'arrêt est interdit sous "
                    "certaines conditions."
                )

        elif description.startswith("\\P"):
            if "EN TOUT TEMPS" in description:
                type_regle = (
                    "STATIONNEMENT_INTERDIT"
                )
                explication = (
                    "Le stationnement est "
                    "interdit en tout temps."
                )
            else:
                type_regle = (
                    "REGLEMENT_CONDITIONNEL"
                )
                explication = (
                    "Le stationnement est "
                    "réglementé selon une "
                    "période ou une exception."
                )

        elif description.startswith("P "):
            type_regle = (
                "STATIONNEMENT_LIMITE"
            )
            explication = (
                "Le stationnement semble "
                "autorisé avec une restriction."
            )

        else:
            type_regle = "INDETERMINE"
            explication = (
                "La règle de ce panneau "
                "n'est pas encore reconnue."
            )

        return {
            "panneau": panneau.vers_dictionnaire(),
            "type_regle": type_regle,
            "explication": explication,
            "interpretation_complete": (type_regle != "INDETERMINE"),
        }

    def obtenir_interpretation(self, identifiant: int) -> dict | None:
        panneau = self.dao.obtenir_par_id(identifiant)

        if panneau is None:
            return None

        return self.interpreter_panneau(
            panneau
        )


    def evaluer_panneau(
            self,
            identifiant: int,
            date_heure: datetime,
    ) -> dict | None:
        panneau = self.dao.obtenir_par_id(
            identifiant
        )

        if panneau is None:
            return None

        return self.evaluer_panneau_modele(
            panneau,
            date_heure,
        )

    @staticmethod
    def determiner_statut(
            interpretation: dict,
            evaluation: dict,
    ) -> dict:
        if not evaluation["analyse_complete"]:
            return {
                "code": "INDETERMINE",
                "stationnement_autorise_selon_ce_panneau": None,
                "message": (
                    "Certaines conditions du panneau "
                    "ne sont pas encore comprises."
                ),
            }

        regle_active = evaluation["regle_active"]

        if regle_active is None:
            return {
                "code": "INDETERMINE",
                "stationnement_autorise_selon_ce_panneau": None,
                "message": (
                    "Le service ne peut pas déterminer "
                    "si la règle est actuellement active."
                ),
            }

        if regle_active is False:
            return {
                "code": "REGLE_INACTIVE",
                "stationnement_autorise_selon_ce_panneau": None,
                "message": (
                    "La règle de ce panneau n'est pas "
                    "active à la date demandée."
                ),
            }

        type_regle = interpretation["type_regle"]

        description = (
            interpretation["panneau"]["description"]
            .strip()
            .upper()
        )

        if (
                type_regle == "ARRET_INTERDIT"
                or description.startswith("\\A")
        ):
            return {
                "code": "ARRET_INTERDIT",
                "stationnement_autorise_selon_ce_panneau": False,
                "message": (
                    "L'arrêt et le stationnement sont "
                    "interdits selon ce panneau."
                ),
            }

        if (
                type_regle == "STATIONNEMENT_INTERDIT"
                or description.startswith("\\P")
        ):
            return {
                "code": "STATIONNEMENT_INTERDIT",
                "stationnement_autorise_selon_ce_panneau": False,
                "message": (
                    "Le stationnement est interdit "
                    "selon ce panneau."
                ),
            }

        if type_regle == "STATIONNEMENT_PAYANT":
            return {
                "code": "STATIONNEMENT_PAYANT",
                "stationnement_autorise_selon_ce_panneau": True,
                "message": (
                    "Le stationnement est autorisé "
                    "avec paiement selon ce panneau."
                ),
            }

        if type_regle == "STATIONNEMENT_LIMITE":
            return {
                "code": "STATIONNEMENT_LIMITE",
                "stationnement_autorise_selon_ce_panneau": True,
                "message": (
                    "Le stationnement est autorisé "
                    "avec une limite selon ce panneau."
                ),
            }

        return {
            "code": "INDETERMINE",
            "stationnement_autorise_selon_ce_panneau": None,
            "message": (
                "Le service ne peut pas déterminer "
                "le statut de ce panneau."
            ),
        }

    def evaluer_panneau_modele(
            self,
            panneau: Panneau,
            date_heure: datetime,
    ) -> dict:
        resultat = self.interpreter_panneau(
            panneau
        )

        evaluation = (
            EvaluateurTemporel
            .evaluer_regle_temporelle(
                panneau.description,
                date_heure,
            )
        )

        resultat["evaluation_temporelle"] = evaluation

        resultat["statut"] = self.determiner_statut(
            resultat,
            evaluation,
        )

        return resultat