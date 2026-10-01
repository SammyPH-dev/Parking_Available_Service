from app.services import ServicePanneaux


def test_distance_coordonnees_identiques():
    distance = (
        ServicePanneaux
        .calculer_distance_metres(
            latitude_1=45.5019,
            longitude_1=-73.5674,
            latitude_2=45.5019,
            longitude_2=-73.5674,
        )
    )

    assert distance == 0


def test_distance_environ_cent_metres():
    distance = (
        ServicePanneaux
        .calculer_distance_metres(
            latitude_1=45.5019,
            longitude_1=-73.5674,
            latitude_2=45.5028,
            longitude_2=-73.5674,
        )
    )

    assert 95 <= distance <= 105