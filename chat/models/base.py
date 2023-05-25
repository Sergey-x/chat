import sqlalchemy as sa

from chat.db import DeclarativeBase


class BaseTable(DeclarativeBase):
    __abstract__ = True

    id = sa.Column(
        sa.Integer,
        primary_key=True,
        doc="Unique index of element",
    )

    def __repr__(self):
        sa.Columns = {sa.Column.name: getattr(self, sa.Column.name) for sa.Column in self.__table__.sa.Columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", sa.Columns.items()))}>'
