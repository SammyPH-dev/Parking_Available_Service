import pytest

from app import creer_application
from app.extensions import db


@pytest.fixture
def application():
    app = creer_application({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": (
            "sqlite:///:memory:"
        ),
    })

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(application):
    return application.test_client()