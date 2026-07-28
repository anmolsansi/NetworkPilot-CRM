from app.schemas.saved_views import SavedViewCreate


def test_saved_view_accepts_invite_and_owner_filters():
    view = SavedViewCreate(
        name="Accepted follow-ups",
        filters={
            "inviteAcceptedOnly": True,
            "ownerId": "00000000-0000-0000-0000-000000000001",
        },
        sort_by="invite_accepted_at",
        sort_order="desc",
    )

    assert view.filters["inviteAcceptedOnly"] is True
    assert view.filters["ownerId"] == "00000000-0000-0000-0000-000000000001"
