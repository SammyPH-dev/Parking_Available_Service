from app.extensions import db


class Panneau(db.Model):
    __tablename__ = "panneaux"

    __table_args__ = (
        db.Index(
            "ix_panneaux_latitude_longitude",
            "latitude",
            "longitude",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    poteau_id = db.Column(
        db.Integer,
        nullable=True,
        index=True,
    )
    code = db.Column(
        db.String(30),
        nullable=True,
        index=True,
    )
    description = db.Column(
        db.String(500),
        nullable=False,
    )
    arrondissement = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )
    latitude = db.Column(
        db.Float,
        nullable=False,
    )
    longitude = db.Column(
        db.Float,
        nullable=False,
    )

    def vers_dictionnaire(self) -> dict:
        return {
            "id": self.id,
            "poteau_id": self.poteau_id,
            "code": self.code,
            "description": self.description,
            "arrondissement": self.arrondissement,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }