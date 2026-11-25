from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    through: str = Field(
        pattern=r"^\d{4}-\d{2}$",
        description="Last closed month with observed sales, format YYYY-MM",
        examples=["2018-12"],
    )
    version: str | None = Field(
        None,
        description="Numeric model version. Defaults to champion alias.",
        examples=["3"],
    )


class ForecastResponse(BaseModel):
    model: str
    version: str
    through: str
    month: str
    predicted_sales: float


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    ready: bool
    model: str | None = None
    version: str | None = None
    detail: str | None = None
