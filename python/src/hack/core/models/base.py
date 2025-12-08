from typing import Annotated

from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


CreatedAt = Annotated[
    datetime,
    mapped_column(default=lambda: datetime.now(tz=timezone.utc))
]
