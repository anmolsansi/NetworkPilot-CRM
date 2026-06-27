from pydantic import BaseModel


class CalendarLinkResponse(BaseModel):
    url: str
    title: str
    description: str
