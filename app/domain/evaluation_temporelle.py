import re
import unicodedata
from datetime import date, datetime, time

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

class EvaluateurTemporel:

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
    def extraire_periode_saisonniere(cls,description: str) -> (
            tuple[
                tuple[int, int],
                tuple[int, int]]
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
    def evaluer_regle_temporelle(cls,description: str,date_heure: datetime,) -> dict:
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