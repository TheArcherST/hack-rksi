from .base import BaseDTO


class ScalarMetricDTO(BaseDTO):
    name: str
    value: float
    unit: str | None = None


class GraphPointDTO(BaseDTO):
    x: str
    y: float


class GraphDTO(BaseDTO):
    name: str
    points: list[GraphPointDTO]


class HistogramBinDTO(BaseDTO):
    label: str
    from_value: float | None = None
    to_value: float | None = None
    count: int


class HistogramDTO(BaseDTO):
    name: str
    bins: list[HistogramBinDTO]


class UserStatisticsDTO(BaseDTO):
    total_events: int
    active_events: int
    past_events: int
    participating_events: int
    rejected_events: int
    upcoming_participations: int
    participation_rate: float


class AdminStatisticsDTO(BaseDTO):
    scalars: list[ScalarMetricDTO]
    graphs: list[GraphDTO]
    histograms: list[HistogramDTO]
