import logging
from datetime import date, timedelta

import pytest

from app.core.errors import ValidationError
from app.services.transition_service import ACTION_TRANSITIONS, calculate_transition

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class TestCalculateTransition:
    def test_invite_sent(self):
        result = calculate_transition("invite_sent")
        assert result.new_stage == "invite_pending"
        assert result.next_action_type == "acceptance_check"
        assert result.next_action_date == date.today() + timedelta(days=1)

    def test_saved_for_later(self):
        result = calculate_transition("saved_for_later")
        assert result.new_stage == "saved_for_later"
        assert result.next_action_type is None
        assert result.next_action_date is None

    def test_invite_sent_custom_delay(self):
        result = calculate_transition("invite_sent", acceptance_check_delay_days=3)
        assert result.next_action_date == date.today() + timedelta(days=3)

    def test_accepted(self):
        result = calculate_transition("accepted")
        assert result.new_stage == "accepted"
        assert result.next_action_type == "send_first_message"
        assert result.next_action_date == date.today()

    def test_message_sent(self):
        result = calculate_transition("message_sent")
        assert result.new_stage == "waiting_for_reply"
        assert result.next_action_type == "follow_up_1"
        assert result.next_action_date == date.today() + timedelta(days=3)

    def test_message_sent_custom_delay(self):
        result = calculate_transition("message_sent", follow_up_delay_days=5)
        assert result.next_action_date == date.today() + timedelta(days=5)

    def test_follow_up_1_sent(self):
        result = calculate_transition("follow_up_1_sent")
        assert result.new_stage == "follow_up_1_sent"
        assert result.next_action_type == "follow_up_2"
        assert result.next_action_date == date.today() + timedelta(days=3)

    def test_reply_received(self):
        result = calculate_transition("reply_received")
        assert result.new_stage == "replied"
        assert result.next_action_type is None
        assert result.next_action_date is None

    def test_invalid_action(self):
        with pytest.raises(ValidationError):
            calculate_transition("invalid_action")

    def test_override_next_action_date(self):
        override_date = date.today() + timedelta(days=10)
        result = calculate_transition("accepted", override_next_action_date=override_date)
        assert result.next_action_date == override_date

    def test_override_next_action_type(self):
        result = calculate_transition("accepted", override_next_action_type="custom_action")
        assert result.next_action_type == "custom_action"

    def test_all_actions_valid(self):
        for action_type in ACTION_TRANSITIONS:
            result = calculate_transition(action_type)
            assert result.new_stage is not None
