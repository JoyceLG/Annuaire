"""table missions

Revision ID: 19d13cabd148
Revises: 007157d67712
Create Date: 2026-09-02 10:20:30.629672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19d13cabd148'
down_revision: Union[str, Sequence[str], None] = '007157d67712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "missions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nom", sa.String(50), nullable=False, unique=True),
        sa.Column("programme", sa.String(50), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=False),
    )

    connexion = op.get_bind()
    connexion.execute(sa.text("""
        INSERT INTO missions (nom, programme, annee)
        SELECT DISTINCT mission, programme, 1970 FROM astronautes
    """))

    op.add_column("astronautes", sa.Column("mission_id", sa.Integer(), nullable=True))

    connexion.execute(sa.text("""
        UPDATE astronautes
        SET mission_id = (SELECT id FROM missions WHERE missions.nom = astronautes.mission)
    """))

    with op.batch_alter_table("astronautes") as batch:
        batch.alter_column("mission_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key("fk_astronaute_mission", "missions", ["mission_id"], ["id"])
        batch.drop_column("mission")
        batch.drop_column("programme")


def downgrade() -> None:
    """Downgrade schema."""
    pass
