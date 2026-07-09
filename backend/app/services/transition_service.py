import logging
from datetime import date, timedelta

from app.core.errors import ValidationError
from app.schemas.activities import TransitionResult

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
# V1 action types and their transitions
ACTION_TRANSITIONS = {
    "saved_for_later": {
        "new_stage": "saved_for_later",
        "next_action_type": None,
        "next_action_date": None,
    },
    "invite_sent": {
        "new_stage": "invite_pending",
        "next_action_type": "acceptance_check",
        "use_acceptance_delay": True,
    },
    "accepted": {
        "new_stage": "accepted",
        "next_action_type": "send_first_message",
        "next_action_date": "today",
    },
    "message_sent": {
        "new_stage": "waiting_for_reply",
        "next_action_type": "follow_up_1",
        "use_follow_up_delay": True,
    },
    "follow_up_1_sent": {
        "new_stage": "follow_up_1_sent",
        "next_action_type": "follow_up_2",
        "use_follow_up_delay": True,
    },
    "reply_received": {
        "new_stage": "replied",
        "next_action_type": None,
        "next_action_date": None,
    },
}


def calculate_transition(
    action_type: str,
    follow_up_delay_days: int = 3,
    acceptance_check_delay_days: int = 1,
    override_next_action_date: date | None = None,
    override_next_action_type: str | None = None,
) -> TransitionResult:
    """
    Calculate stage transition based on action type.

    Args:
        action_type: The action being performed
        follow_up_delay_days: Default days for follow-up
        acceptance_check_delay_days: Default days for acceptance check
        override_next_action_date: Override next action date
        override_next_action_type: Override next action type

    Returns:
        TransitionResult with new stage and next action

    Raises:
        ValidationError: If action type is invalid
    """
    if action_type not in ACTION_TRANSITIONS:
        raise ValidationError(
            f"Invalid action type: {action_type}",
            details={"valid_actions": list(ACTION_TRANSITIONS.keys())},
        )

    rule = ACTION_TRANSITIONS[action_type]
    new_stage = rule["new_stage"]

    # Determine next action date
    next_action_date = override_next_action_date
    if next_action_date is None:
        if rule.get("next_action_date") == "today":
            next_action_date = date.today()
        elif rule.get("use_follow_up_delay"):
            next_action_date = date.today() + timedelta(days=follow_up_delay_days)
        elif rule.get("use_acceptance_delay"):
            next_action_date = date.today() + timedelta(days=acceptance_check_delay_days)

    # Determine next action type
    next_action_type = override_next_action_type or rule.get("next_action_type")

    return TransitionResult(
        new_stage=new_stage,
        next_action_type=next_action_type,
        next_action_date=next_action_date,
    )
