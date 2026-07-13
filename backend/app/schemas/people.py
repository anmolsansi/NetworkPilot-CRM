import logging
import uuid
from datetime import date, datetime
from typing import Annotated, Literal, Union
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.tag import TagResponse

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    linkedin_url: str = Field(..., min_length=1)
    role: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=200)
    email: str | None = Field(None, max_length=320)
    phone_number: str | None = Field(None, max_length=100)
    premium: bool | None = None
    company_website: str | None = None
    processed_at: datetime | None = None
    processed_at_millis: int | None = None
    invite_accepted_at: datetime | None = None
    invite_accepted_at_millis: int | None = None
    is_favorite: bool = False
    favorite_notes: str | None = None
    priority: str = Field(default="B", pattern=r"^[ABC]$")
    connection_note: str | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = Field(None, max_length=20)


class PersonUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    role: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=200)
    email: str | None = Field(None, max_length=320)
    phone_number: str | None = Field(None, max_length=100)
    premium: bool | None = None
    company_website: str | None = None
    is_favorite: bool | None = None
    favorite_notes: str | None = None
    priority: str | None = Field(None, pattern=r"^[ABC]$")
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = Field(None, max_length=20)


class PersonResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    first_name: str | None
    last_name: str | None
    linkedin_url: str
    linkedin_slug: str
    role: str | None
    company: str | None
    location: str | None
    email: str | None
    phone_number: str | None
    premium: bool | None
    company_website: str | None
    processed_at: datetime | None
    processed_at_millis: int | None
    invite_accepted_at: datetime | None
    invite_accepted_at_millis: int | None
    is_favorite: bool
    favorite_notes: str | None
    priority: str
    stage: str
    status: str
    next_action_type: str | None
    next_action_date: date | None
    last_action_type: str | None
    last_action_date: date | None
    connection_note: str | None
    notes: str | None
    tags: list["TagResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonListResponse(BaseModel):
    items: list[PersonResponse]
    total: int
    page: int
    limit: int


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BulkSetFavoritePayload(StrictModel):
    is_favorite: bool


class BulkTagsPayload(StrictModel):
    tag_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=20)

    @field_validator("tag_ids")
    @classmethod
    def require_unique_tags(cls, tag_ids: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(set(tag_ids)) != len(tag_ids):
            raise ValueError("Select each tag only once.")
        return tag_ids


class BulkPriorityPayload(StrictModel):
    priority: Literal["A", "B", "C"]


class BulkStagePayload(StrictModel):
    stage: Literal[
        "saved_for_later",
        "invite_sent",
        "invite_pending",
        "accepted",
        "waiting_for_reply",
        "replied",
        "archived",
    ]


class BulkArchivePayload(StrictModel):
    pass


class BulkNextActionPayload(StrictModel):
    next_action_type: str | None = Field(None, max_length=100)
    next_action_date: date | None = None

    @field_validator("next_action_type", mode="before")
    @classmethod
    def normalize_next_action_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class BulkPeopleActionBase(StrictModel):
    workspace_id: uuid.UUID
    person_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)

    @field_validator("person_ids")
    @classmethod
    def require_unique_people(cls, person_ids: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(set(person_ids)) != len(person_ids):
            raise ValueError("Select each person only once.")
        return person_ids


class BulkSetFavoriteRequest(BulkPeopleActionBase):
    action: Literal["set_favorite"]
    payload: BulkSetFavoritePayload


class BulkAddTagsRequest(BulkPeopleActionBase):
    action: Literal["add_tags"]
    payload: BulkTagsPayload


class BulkRemoveTagsRequest(BulkPeopleActionBase):
    action: Literal["remove_tags"]
    payload: BulkTagsPayload


class BulkSetPriorityRequest(BulkPeopleActionBase):
    action: Literal["set_priority"]
    payload: BulkPriorityPayload


class BulkSetStageRequest(BulkPeopleActionBase):
    action: Literal["set_stage"]
    payload: BulkStagePayload


class BulkArchiveRequest(BulkPeopleActionBase):
    action: Literal["archive"]
    payload: BulkArchivePayload


class BulkSetNextActionRequest(BulkPeopleActionBase):
    action: Literal["set_next_action"]
    payload: BulkNextActionPayload


BulkPeopleActionRequest = Annotated[
    Union[
        BulkSetFavoriteRequest,
        BulkAddTagsRequest,
        BulkRemoveTagsRequest,
        BulkSetPriorityRequest,
        BulkSetStageRequest,
        BulkArchiveRequest,
        BulkSetNextActionRequest,
    ],
    Field(discriminator="action"),
]


class BulkPeopleActionResponse(BaseModel):
    updated_count: int
    items: list[PersonResponse]


class SnoozeRequest(BaseModel):
    until_date: date = Field(..., description="Date to snooze until")
    notes: str | None = None


class ArchiveRequest(BaseModel):
    notes: str | None = None
