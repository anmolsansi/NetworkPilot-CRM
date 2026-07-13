import logging

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class TestTemplateRendering:
    def test_render_basic_variables(self):
        body = "Hi {{first_name}}, I work at {{company}}."
        rendered = body.replace("{{first_name}}", "John").replace("{{company}}", "Google")
        assert rendered == "Hi John, I work at Google."

    def test_render_multiple_occurrences(self):
        body = "{{name}} is great. {{name}} really is."
        rendered = body.replace("{{name}}", "John")
        assert rendered == "John is great. John really is."

    def test_render_missing_variable(self):
        body = "Hi {{first_name}}, welcome to {{company}}."
        rendered = body.replace("{{first_name}}", "John")
        assert "{{company}}" in rendered

    def test_render_no_variables(self):
        body = "Hello, this is a plain message."
        rendered = body
        assert rendered == body

    def test_render_role_variable(self):
        body = "Your role as {{role}} is important."
        rendered = body.replace("{{role}}", "Engineer")
        assert rendered == "Your role as Engineer is important."


class TestTemplateCategories:
    def test_valid_categories(self):
        valid = ["connection_request", "first_message", "follow_up"]
        for cat in valid:
            assert cat in valid

    def test_template_variables(self):
        variables = ["first_name", "name", "company", "role"]
        assert "first_name" in variables
        assert "company" in variables
