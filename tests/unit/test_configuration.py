def test_configuration_test_remplace_defauts(
    application,
):
    assert application.config["TESTING"] is True

    assert (
        application.config[
            "SQLALCHEMY_DATABASE_URI"
        ]
        == "sqlite:///:memory:"
    )

    assert (
        application.config["API_PREFIXE"]
        == "/api/v1"
    )

    assert (
        application.config["FUSEAU_HORAIRE"]
        == "America/Toronto"
    )