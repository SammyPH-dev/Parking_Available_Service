from app.domain.geographie import (
    calculer_distance_metres,
    calculer_limites_recherche,
)


def test_distance_coordonnees_identiques():
    distance = calculer_distance_metres(
        latitude_1=45.5019,
        longitude_1=-73.5674,
        latitude_2=45.5019,
        longitude_2=-73.5674,
    )

    assert distance == 0


def test_distance_environ_cent_metres():
    distance = calculer_distance_metres(
        latitude_1=45.5019,
        longitude_1=-73.5674,
        latitude_2=45.5028,
        longitude_2=-73.5674,
    )

    assert 95 <= distance <= 105


def test_limites_recherche_encadrent_position():
    (
        latitude_min,
        latitude_max,
        longitude_min,
        longitude_max,
    ) = calculer_limites_recherche(
        latitude=45.5019,
        longitude=-73.5674,
        rayon_metres=500,
    )

    assert latitude_min < 45.5019 < latitude_max
    assert longitude_min < -73.5674 < longitude_max