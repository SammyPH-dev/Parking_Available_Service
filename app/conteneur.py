from dataclasses import dataclass
from typing import cast

from flask import current_app

from app.dao import PanneauDAO
from app.services import (
    ServicePanneaux,
    ServicePoteaux,
)


@dataclass(frozen=True)
class ServicesApplication:
    panneaux: ServicePanneaux
    poteaux: ServicePoteaux


def creer_services_application(
) -> ServicesApplication:
    panneau_dao = PanneauDAO()

    service_panneaux = ServicePanneaux(
        panneau_dao
    )

    service_poteaux = ServicePoteaux(
        dao=panneau_dao,
        service_panneaux=service_panneaux,
    )

    return ServicesApplication(
        panneaux=service_panneaux,
        poteaux=service_poteaux,
    )


def obtenir_services_application(
) -> ServicesApplication:
    return cast(
        ServicesApplication,
        current_app.extensions[
            "services_application"
        ],
    )