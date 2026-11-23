
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task import Task


# Junction table connecting tasks and labels.
task_labels = Table(
    "task_labels",
    Base.metadata,
    Column(
        "task_id",
        Integer,
        ForeignKey("tasks.id"),
        primary_key=True,
    ),
    Column(
        "label_id",
        Integer,
        ForeignKey("labels.id"),
        primary_key=True,
    ),
)



class Label(Base):
    __tablename__ = "labels"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            name="uq_project_label_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )

    project: Mapped["Project"] = relationship(
        back_populates="labels"
    )

    tasks: Mapped[list["Task"]] = relationship(
        secondary=task_labels,
        back_populates="labels",
    )
