from datetime import datetime, timezone
from typing import Iterable

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hack.core.models import Event, EventParticipant
from hack.rest_server.models import AuthorizedAdministrator, AuthorizedUser
from hack.rest_server.schemas.statistics import (
    AdminStatisticsDTO,
    GraphDTO,
    GraphPointDTO,
    HistogramBinDTO,
    HistogramDTO,
    ScalarMetricDTO,
    UserStatisticsDTO,
)


userspace_router = APIRouter(
    prefix="/users",
)
admin_router = APIRouter()


def _safe_int(value: int | None) -> int:
    return int(value or 0)


def _safe_float(value: float | None) -> float:
    return float(value or 0.0)


@userspace_router.get(
    "/me/statistics",
    response_model=UserStatisticsDTO,
)
@inject
async def get_my_statistics(
    session: FromDishka[AsyncSession],
    authorized_user: FromDishka[AuthorizedUser],
) -> UserStatisticsDTO:
    now = datetime.now(tz=timezone.utc)

    events_counts_stmt = (
        select(
            func.count(Event.id).label("total_events"),
            func.count(Event.id)
            .filter(Event.ends_at > now)
            .label("active_events"),
            func.count(Event.id)
            .filter(Event.ends_at <= now)
            .label("past_events"),
        )
        .where(Event.rejected_at.is_(None))
    )
    events_counts = (await session.execute(events_counts_stmt)).one()

    participation_counts_stmt = (
        select(
            func.count(EventParticipant.id)
            .filter(
                EventParticipant.status
                == EventParticipant.ParticipationStatusEnum.PARTICIPATING,
            )
            .label("participating_events"),
            func.count(EventParticipant.id)
            .filter(
                and_(
                    EventParticipant.status
                    == EventParticipant.ParticipationStatusEnum.PARTICIPATING,
                    Event.ends_at > now,
                ),
            )
            .label("upcoming_participations"),
        )
        .join(Event, Event.id == EventParticipant.event_id)
        .where(EventParticipant.user_id == authorized_user.id)
        .where(Event.rejected_at.is_(None))
    )
    participation_counts = (await session.execute(participation_counts_stmt)).one()

    total_events = _safe_int(events_counts.total_events)
    participating_events = _safe_int(participation_counts.participating_events)
    participation_rate = (
        participating_events / total_events
        if total_events
        else 0.0
    )

    return UserStatisticsDTO(
        total_events=total_events,
        active_events=_safe_int(events_counts.active_events),
        past_events=_safe_int(events_counts.past_events),
        participating_events=participating_events,
        rejected_events=0,
        upcoming_participations=_safe_int(
            participation_counts.upcoming_participations,
        ),
        participation_rate=participation_rate,
    )


def _build_participants_histogram(
    event_rows: Iterable[tuple],
) -> HistogramDTO:
    buckets = [
        ("0", 0, 0),
        ("1", 1, 1),
        ("2-3", 2, 3),
        ("4-5", 4, 5),
        ("6+", 6, None),
    ]
    bins: list[HistogramBinDTO] = []
    for label, start, end in buckets:
        count = 0
        for row in event_rows:
            participants_count = _safe_int(
                getattr(row, "participants_count", 0),
            )
            if end is None:
                if participants_count >= start:
                    count += 1
            elif start <= participants_count <= end:
                count += 1
        bins.append(
            HistogramBinDTO(
                label=label,
                from_value=float(start),
                to_value=float(end) if end is not None else None,
                count=count,
            )
        )
    return HistogramDTO(
        name="participants_per_event",
        bins=bins,
    )


def _build_fill_rate_histogram(
    event_rows: Iterable[tuple],
) -> HistogramDTO:
    buckets = [
        ("0-25%", 0.0, 0.25),
        ("25-50%", 0.25, 0.5),
        ("50-75%", 0.5, 0.75),
        ("75-100%", 0.75, 1.0),
        ("100%+", 1.0, None),
    ]
    bins: list[HistogramBinDTO] = []
    rates: list[float] = []
    for row in event_rows:
        max_participants_count = getattr(row, "max_participants_count", None)
        if not max_participants_count:
            continue
        participants_count = _safe_int(
            getattr(row, "participants_count", 0),
        )
        rates.append(
            participants_count / max_participants_count,
        )

    for label, start, end in buckets:
        count = 0
        for rate in rates:
            if end is None:
                if rate >= start:
                    count += 1
            elif start <= rate < end:
                count += 1
        bins.append(
            HistogramBinDTO(
                label=label,
                from_value=start,
                to_value=end,
                count=count,
            )
        )

    return HistogramDTO(
        name="capacity_fill_rate",
        bins=bins,
    )


@admin_router.get(
    "/statistics",
    response_model=AdminStatisticsDTO,
)
@inject
async def get_statistics(
    session: FromDishka[AsyncSession],
    _authorized_administrator: FromDishka[AuthorizedAdministrator],
) -> AdminStatisticsDTO:
    now = datetime.now(tz=timezone.utc)

    events_counts_stmt = (
        select(
            func.count(Event.id)
            .filter(Event.rejected_at.is_(None))
            .label("events_total"),
            func.count(Event.id)
            .filter(Event.rejected_at.is_not(None))
            .label("rejected_events"),
            func.count(Event.id)
            .filter(and_(Event.rejected_at.is_(None), Event.ends_at > now))
            .label("active_events"),
            func.count(Event.id)
            .filter(and_(Event.rejected_at.is_(None), Event.ends_at <= now))
            .label("past_events"),
        )
    )
    events_counts = (await session.execute(events_counts_stmt)).one()

    participation_totals_stmt = (
        select(
            func.count(EventParticipant.id)
            .filter(
                EventParticipant.status
                == EventParticipant.ParticipationStatusEnum.PARTICIPATING,
            )
            .label("total_participations"),
            func.count(func.distinct(EventParticipant.user_id))
            .filter(
                EventParticipant.status
                == EventParticipant.ParticipationStatusEnum.PARTICIPATING,
            )
            .label("unique_participants"),
        )
        .join(Event, Event.id == EventParticipant.event_id, isouter=True)
        .where(Event.rejected_at.is_(None))
    )
    participation_totals = (await session.execute(participation_totals_stmt)).one()

    event_agg_subq = (
        select(
            Event.id.label("event_id"),
            Event.max_participants_count.label("max_participants_count"),
            func.date(Event.starts_at).label("start_date"),
            func.count(EventParticipant.id)
            .filter(
                EventParticipant.status
                == EventParticipant.ParticipationStatusEnum.PARTICIPATING,
            )
            .label("participants_count"),
        )
        .outerjoin(EventParticipant, EventParticipant.event_id == Event.id)
        .where(Event.rejected_at.is_(None))
        .group_by(Event.id, Event.max_participants_count, func.date(Event.starts_at))
    ).subquery()

    event_rows = list(await session.execute(select(event_agg_subq)))
    event_rows_values = [row for row in event_rows]
    total_participants = sum(
        _safe_int(getattr(row, "participants_count", 0))
        for row in event_rows_values
    )
    avg_participants_per_event = (
        total_participants / len(event_rows_values)
        if event_rows_values
        else 0.0
    )

    timeline_stmt = (
        select(
            event_agg_subq.c.start_date.label("start_date"),
            func.count(event_agg_subq.c.event_id).label("events"),
            func.coalesce(
                func.sum(event_agg_subq.c.participants_count),
                0,
            ).label("participants"),
        )
        .group_by(event_agg_subq.c.start_date)
        .order_by(event_agg_subq.c.start_date)
    )
    timeline_rows = await session.execute(timeline_stmt)
    timeline_rows = list(timeline_rows)

    graphs = [
        GraphDTO(
            name="events_by_start_date",
            points=[
                GraphPointDTO(
                    x=row.start_date.isoformat(),
                    y=_safe_float(row.events),
                )
                for row in timeline_rows
                if row.start_date is not None
            ],
        ),
        GraphDTO(
            name="participants_by_start_date",
            points=[
                GraphPointDTO(
                    x=row.start_date.isoformat(),
                    y=_safe_float(row.participants),
                )
                for row in timeline_rows
                if row.start_date is not None
            ],
        ),
    ]

    histograms = [
        _build_participants_histogram(event_rows_values),
        _build_fill_rate_histogram(event_rows_values),
    ]

    scalars = [
        ScalarMetricDTO(name="events_total", value=_safe_int(events_counts.events_total)),
        ScalarMetricDTO(name="active_events", value=_safe_int(events_counts.active_events)),
        ScalarMetricDTO(name="past_events", value=_safe_int(events_counts.past_events)),
        ScalarMetricDTO(name="rejected_events", value=_safe_int(events_counts.rejected_events)),
        ScalarMetricDTO(
            name="total_participations",
            value=_safe_int(participation_totals.total_participations),
        ),
        ScalarMetricDTO(
            name="unique_participants",
            value=_safe_int(participation_totals.unique_participants),
        ),
        ScalarMetricDTO(
            name="avg_participants_per_event",
            value=avg_participants_per_event,
        ),
    ]

    return AdminStatisticsDTO(
        scalars=scalars,
        graphs=graphs,
        histograms=histograms,
    )
