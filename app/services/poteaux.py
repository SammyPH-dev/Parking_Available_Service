from datetime import datetime

from app.dao import PanneauDAO
from app.domain.geographie import (
    calculer_distance_metres,
    calculer_limites_recherche,
    valider_recherche_geographique,
)
from app.services.panneaux import (
    ServicePanneaux,
)


class ServicePoteaux:
    def __init__(
        self,
        dao: PanneauDAO,
        service_panneaux: ServicePanneaux,
    ) -> None:
        self.dao = dao
        self.service_panneaux = (
            service_panneaux
        )

    @staticmethod
    def determiner_statut_poteau(
            evaluations: list[dict],
    ) -> dict:
        codes = {
            evaluation["statut"]["code"]
            for evaluation in evaluations
        }

        if "ARRET_INTERDIT" in codes:
            return {
                "code": "ARRET_INTERDIT",
                "stationnement_autorise_selon_ce_poteau": False,
                "message": (
                    "Au moins un panneau actif "
                    "interdit l'arrêt."
                ),
            }

        if "STATIONNEMENT_INTERDIT" in codes:
            return {
                "code": "STATIONNEMENT_INTERDIT",
                "stationnement_autorise_selon_ce_poteau": False,
                "message": (
                    "Au moins un panneau actif "
                    "interdit le stationnement."
                ),
            }

        if "INDETERMINE" in codes:
            return {
                "code": "INDETERMINE",
                "stationnement_autorise_selon_ce_poteau": None,
                "message": (
                    "Au moins un panneau ne peut "
                    "pas être interprété complètement."
                ),
            }

        conditions = {
            "STATIONNEMENT_PAYANT",
            "STATIONNEMENT_LIMITE",
        }

        if codes.intersection(conditions):
            return {
                "code": "AUTORISE_AVEC_CONDITIONS",
                "stationnement_autorise_selon_ce_poteau": True,
                "message": (
                    "Le stationnement semble autorisé "
                    "avec certaines conditions."
                ),
            }

        return {
            "code": "AUCUNE_REGLE_ACTIVE",
            "stationnement_autorise_selon_ce_poteau": None,
            "message": (
                "Aucune restriction active n'a été "
                "détectée sur ce poteau."
            ),
        }


    def evaluer_poteau(
            self,
            poteau_id: int,
            date_heure: datetime,
    ) -> dict | None:
        panneaux = self.dao.lister_par_poteau(
            poteau_id
        )

        if not panneaux:
            return None

        evaluations = [
            self.service_panneaux.evaluer_panneau_modele(
                panneau,
                date_heure,
            )
            for panneau in panneaux
        ]

        return {
            "poteau_id": poteau_id,
            "nombre_panneaux": len(evaluations),
            "statut_global": (
                self.determiner_statut_poteau(
                    evaluations
                )
            ),
            "evaluations": evaluations,
        }

    def trouver_poteaux_proches(
            self,
            latitude: float,
            longitude: float,
            date_heure: datetime,
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

        groupes = {}
        distances = {}

        for panneau in candidats:
            distance = calculer_distance_metres(
                latitude,
                longitude,
                panneau.latitude,
                panneau.longitude,
            )

            if distance > rayon_metres:
                continue

            if panneau.poteau_id is not None:
                cle = ("poteau", panneau.poteau_id)
            else:
                # Un panneau sans poteau devient son propre groupe.
                cle = ("panneau", panneau.id)

            groupes.setdefault(cle, []).append(
                panneau
            )

            if (
                    cle not in distances
                    or distance < distances[cle]
            ):
                distances[cle] = distance

        cles_triees = sorted(
            groupes,
            key=lambda cle: distances[cle],
        )

        resultats = []

        for cle in cles_triees[:limite]:
            panneaux = groupes[cle]

            evaluations = [
                self.service_panneaux.evaluer_panneau_modele(
                    panneau,
                    date_heure,
                )
                for panneau in panneaux
            ]

            premier_panneau = panneaux[0]

            resultats.append({
                "poteau_id": premier_panneau.poteau_id,
                "latitude": premier_panneau.latitude,
                "longitude": premier_panneau.longitude,
                "distance_metres": round(
                    distances[cle],
                    1,
                ),
                "nombre_panneaux": len(panneaux),
                "statut_global": (
                    self.determiner_statut_poteau(
                        evaluations
                    )
                ),
                "evaluations": evaluations,
            })

        return resultats