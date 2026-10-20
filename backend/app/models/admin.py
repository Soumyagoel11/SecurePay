"""Admin profile model (extends User)."""

from app.extensions import db
from app.models.user import User


class Admin(db.Model):
    __tablename__ = "admins"

    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    department = db.Column(db.String(100), nullable=True)

    user = db.relationship("User", backref=db.backref("admin", uselist=False))

    def to_dict(self):
        return {
            "admin_id": self.admin_id,
            "user_id": self.user_id,
            "department": self.department,
            "email": self.user.email if self.user else None,
        }
