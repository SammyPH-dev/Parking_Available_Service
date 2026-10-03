from math import asin, cos, radians, sin, sqrt


RAYON_TERRE_METRES = 6_371_000
METRES_PAR_DEGRE = 111_320


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
def calculer_limites_recherche(
    latitude: float,
    longitude: float,
    rayon_metres: int,
) -> tuple[float, float, float, float]:
    variation_latitude = (
        rayon_metres / METRES_PAR_DEGRE
    )

    variation_longitude = rayon_metres / (
        METRES_PAR_DEGRE
        * cos(radians(latitude))
    )

    return (
        latitude - variation_latitude,
        latitude + variation_latitude,
        longitude - variation_longitude,
        longitude + variation_longitude,
    )

def valider_recherche_geographique(
    latitude: float,
    longitude: float,
    rayon_metres: int,
    limite: int,
) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError(
            "La latitude doit être comprise "
            "entre -90 et 90."
        )

    if not -180 <= longitude <= 180:
        raise ValueError(
            "La longitude doit être comprise "
            "entre -180 et 180."
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
            "La limite doit être comprise "
            "entre 1 et 100."
        )