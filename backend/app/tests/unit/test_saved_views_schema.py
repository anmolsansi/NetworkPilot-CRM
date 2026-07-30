import pytest
from pydantic import ValidationError

from app.schemas.saved_views import SavedViewCreate


def test_saved_view_accepts_invite_and_owner_filters():
    view = SavedViewCreate(
        name="Accepted follow-ups",
        filters={
            "inviteAcceptedMissing": True,
            "emailMissing": True,
            "ownerId": "00000000-0000-0000-0000-000000000001",
        },
        sort_by="invite_accepted_at",
        sort_order="desc",
    )

    assert view.filters["inviteAcceptedMissing"] is True
    assert view.filters["emailMissing"] is True
    assert view.filters["ownerId"] == "00000000-0000-0000-0000-000000000001"


def test_saved_view_rejects_conflicting_presence_filters():
    with pytest.raises(ValidationError):
        SavedViewCreate(
            name="Invalid presence filters",
            filters={"emailPresent": True, "emailMissing": True},
            sort_by="email",
            sort_order="asc",
        )
