import unicodedata
import re
from app.models import Panneau
from app.dao import PanneauDAO
from math import asin, cos, radians, sin, sqrt
from datetime import datetime, time, date

RAYON_TERRE_METRES = 6_371_000

JOURS_SEMAINE = {
    "LUN": 0,
    "LUNDI": 0,
    "MAR": 1,
    "MARDI": 1,
    "MER": 2,
    "MERCREDI": 2,
    "JEU": 3,
    "JEUDI": 3,
    "VEN": 4,
    "VENDREDI": 4,
    "SAM": 5,
    "SAMEDI": 5,
    "DIM": 6,
    "DIMANCHE": 6,
}

MOIS_ANNEE = {
    "JANVIER": 1,
    "FEVRIER": 2,
    "MARS": 3,
    "AVRIL": 4,
    "MAI": 5,
    "JUIN": 6,
    "JUILLET": 7,
    "AOUT": 8,
    "SEPTEMBRE": 9,
    "OCTOBRE": 10,
    "NOVEMBRE": 11,
    "DECEMBRE": 12,
    "DEC": 12,
}

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

    @staticmethod
    def extraire_plage_horaire(description: str) -> tuple[time, time] | None:
        motif = (
            r"(\d{1,2})h(\d{2})?"
            r"\s*-\s*"
            r"(\d{1,2})h(\d{2})?"
        )

        correspondance = re.search(
            motif,
            description,
            flags=re.IGNORECASE,
        )

        if correspondance is None:
            return None

        heure_debut = int(correspondance.group(1))
        minute_debut = int(correspondance.group(2) or 0)
        heure_fin = int(correspondance.group(3))
        minute_fin = int(correspondance.group(4) or 0)

        try:
            debut = time(
                hour=heure_debut,
                minute=minute_debut,
            )
            fin = time(
                hour=heure_fin,
                minute=minute_fin,
            )
        except ValueError:
            return None

        return debut, fin

    @staticmethod
    def heure_dans_plage(heure_actuelle: time,debut: time,fin: time) -> bool:
        if debut <= fin:
            return (
                    debut
                    <= heure_actuelle
                    < fin
            )

        return (
                heure_actuelle >= debut
                or heure_actuelle < fin
        )

    @classmethod
    def evaluer_plage_horaire(cls,description: str, date_heure: datetime) -> dict:
        plage = cls.extraire_plage_horaire(description)

        if plage is None:
            return {
                "plage_horaire_trouvee": False,
                "debut": None,
                "fin": None,
                "heure_dans_plage": None,
            }

        debut, fin = plage

        est_dans_plage = (
            cls.heure_dans_plage(
                heure_actuelle=(
                    date_heure.time()
                ),
                debut=debut,
                fin=fin,
            )
        )

        return {
            "plage_horaire_trouvee": True,
            "debut": debut.strftime("%H:%M"),
            "fin": fin.strftime("%H:%M"),
            "heure_dans_plage": (
                est_dans_plage
            ),
        }

    @staticmethod
    def extraire_jours_semaine(description: str) -> set[int] | None:
        texte = (
            description
            .upper()
            .replace(".", "")
        )

        lundi_au_vendredi = re.search(
            (
                r"\bLUN(?:DI)?\s+"
                r"(?:A|AU)\s+"
                r"VEN(?:DREDI)?\b"
            ),
            texte,
        )

        if lundi_au_vendredi:
            return {0, 1, 2, 3, 4}

        lundi_au_samedi = re.search(
            (
                r"\bLUN(?:DI)?\s+"
                r"(?:A|AU)\s+"
                r"SAM(?:EDI)?\b"
            ),
            texte,
        )

        if lundi_au_samedi:
            return {0, 1, 2, 3, 4, 5}

        motif_jour = (
            r"\b("
            r"LUNDI|LUN|"
            r"MARDI|MAR|"
            r"MERCREDI|MER|"
            r"JEUDI|JEU|"
            r"VENDREDI|VEN|"
            r"SAMEDI|SAM|"
            r"DIMANCHE|DIM"
            r")\b"
        )

        jours_trouves = re.findall(
            motif_jour,
            texte,
        )

        if not jours_trouves:
            return None

        return {
            JOURS_SEMAINE[jour]
            for jour in jours_trouves
        }

    @classmethod
    def evaluer_jour_semaine(cls,description: str,date_heure: datetime) -> dict:
        jours = cls.extraire_jours_semaine(
            description
        )

        if jours is None:
            return {
                "jours_trouves": False,
                "jours": [],
                "jour_correspond": None,
            }

        jour_actuel = date_heure.weekday()

        noms_jours = [
            "LUNDI",
            "MARDI",
            "MERCREDI",
            "JEUDI",
            "VENDREDI",
            "SAMEDI",
            "DIMANCHE",
        ]

        return {
            "jours_trouves": True,
            "jours": [
                noms_jours[jour]
                for jour in sorted(jours)
            ],
            "jour_correspond": (
                    jour_actuel in jours
            ),
        }

    @staticmethod
    def normaliser_texte(
            texte: str,
    ) -> str:
        texte_majuscule = texte.upper()

        texte_decompose = (
            unicodedata.normalize(
                "NFD",
                texte_majuscule,
            )
        )

        return "".join(
            caractere
            for caractere in texte_decompose
            if unicodedata.category(
                caractere
            ) != "Mn"
        )

    @classmethod
    def extraire_periode_saisonniere(
            cls,
            description: str,
    ) -> (
            tuple[
                tuple[int, int],
                tuple[int, int],
            ]
            | None
    ):
        texte = cls.normaliser_texte(
            description
        )

        noms_mois = (
            r"JANVIER|FEVRIER|MARS|"
            r"AVRIL|MAI|JUIN|JUILLET|"
            r"AOUT|SEPTEMBRE|OCTOBRE|"
            r"NOVEMBRE|DECEMBRE|DEC"
        )

        motif = (
            rf"\b(\d{{1,2}})\s*"
            rf"({noms_mois})"
            rf"\s+(?:A|AU)\s+"
            rf"(\d{{1,2}})\s*"
            rf"({noms_mois})\b"
        )

        correspondance = re.search(
            motif,
            texte,
        )

        if correspondance is None:
            return None

        jour_debut = int(
            correspondance.group(1)
        )
        mois_debut = MOIS_ANNEE[
            correspondance.group(2)
        ]

        jour_fin = int(
            correspondance.group(3)
        )
        mois_fin = MOIS_ANNEE[
            correspondance.group(4)
        ]

        try:
            date(
                2000,
                mois_debut,
                jour_debut,
            )
            date(
                2000,
                mois_fin,
                jour_fin,
            )
        except ValueError:
            return None

        return (
            (mois_debut, jour_debut),
            (mois_fin, jour_fin),
        )

    @staticmethod
    def date_dans_periode(
            date_actuelle: date,
            debut: tuple[int, int],
            fin: tuple[int, int],
    ) -> bool:
        valeur_actuelle = (
            date_actuelle.month,
            date_actuelle.day,
        )

        if debut <= fin:
            return (
                    debut
                    <= valeur_actuelle
                    <= fin
            )

        return (
                valeur_actuelle >= debut
                or valeur_actuelle <= fin
        )

    @classmethod
    def evaluer_periode_saisonniere(
            cls,
            description: str,
            date_heure: datetime,
    ) -> dict:
        periode = (
            cls.extraire_periode_saisonniere(
                description
            )
        )

        if periode is None:
            return {
                "periode_trouvee": False,
                "debut": None,
                "fin": None,
                "date_dans_periode": None,
            }

        debut, fin = periode

        est_dans_periode = (
            cls.date_dans_periode(
                date_actuelle=(
                    date_heure.date()
                ),
                debut=debut,
                fin=fin,
            )
        )

        return {
            "periode_trouvee": True,
            "debut": {
                "mois": debut[0],
                "jour": debut[1],
            },
            "fin": {
                "mois": fin[0],
                "jour": fin[1],
            },
            "date_dans_periode": (
                est_dans_periode
            ),
        }

    @classmethod
    def evaluer_regle_temporelle(
            cls,
            description: str,
            date_heure: datetime,
    ) -> dict:
        evaluation_horaire = cls.evaluer_plage_horaire(
            description,
            date_heure,
        )

        evaluation_jour = cls.evaluer_jour_semaine(
            description,
            date_heure,
        )

        evaluation_periode = cls.evaluer_periode_saisonniere(
            description,
            date_heure,
        )

        conditions = []

        if evaluation_horaire["plage_horaire_trouvee"]:
            conditions.append(evaluation_horaire["heure_dans_plage"])

        if evaluation_jour["jours_trouves"]:
            conditions.append(evaluation_jour["jour_correspond"])

        if evaluation_periode["periode_trouvee"]:
            conditions.append(evaluation_periode["date_dans_periode"])

        description_normalisee = cls.normaliser_texte(description)

        en_tout_temps = (
                "EN TOUT TEMPS"
                in description_normalisee
        )

        if en_tout_temps:
            regle_active = True
        elif conditions:
            regle_active = all(conditions)
        else:
            regle_active = None

        expressions_non_supportees = [
            "EXCEPTE",
            "JOURS D'ECOLE",
            "CLIGNOTANT",
            "FLEXIBLE",
            "AUX AUTOBUS",
        ]

        expressions_detectees = [
            expression
            for expression in expressions_non_supportees
            if expression in description_normalisee
        ]

        condition_temporelle_trouvee = (
                en_tout_temps
                or bool(conditions)
        )

        analyse_complete = (
                condition_temporelle_trouvee
                and len(expressions_detectees) == 0
        )

        return {
            "regle_active": regle_active,
            "en_tout_temps": en_tout_temps,
            "analyse_complete": analyse_complete,
            "expressions_non_supportees": expressions_detectees,
            "horaire": evaluation_horaire,
            "jours": evaluation_jour,
            "periode": evaluation_periode,
        }

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

        return self._evaluer_objet_panneau(
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

    def _evaluer_objet_panneau(
            self,
            panneau: Panneau,
            date_heure: datetime,
    ) -> dict:
        resultat = self.interpreter_panneau(
            panneau
        )

        evaluation = self.evaluer_regle_temporelle(
            panneau.description,
            date_heure,
        )

        resultat["evaluation_temporelle"] = evaluation

        resultat["statut"] = self.determiner_statut(
            resultat,
            evaluation,
        )

        return resultat

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
            self._evaluer_objet_panneau(
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

        groupes = {}
        distances = {}

        for panneau in candidats:
            distance = self.calculer_distance_metres(
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
                self._evaluer_objet_panneau(
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