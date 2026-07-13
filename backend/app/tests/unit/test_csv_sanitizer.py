import logging

from app.services.csv_sanitizer import sanitize_csv_value, write_csv

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class TestCsvSanitizer:
    def test_prefixes_formula_like_values(self):
        assert sanitize_csv_value("=IMPORTXML('x')") == "'=IMPORTXML('x')"
        assert sanitize_csv_value("+cmd") == "'+cmd"
        assert sanitize_csv_value("-cmd") == "'-cmd"
        assert sanitize_csv_value("@cmd") == "'@cmd"

    def test_leaves_safe_values_unchanged(self):
        assert sanitize_csv_value("Example Inc") == "Example Inc"
        assert sanitize_csv_value(["backend", "referral"]) == "backend; referral"

    def test_write_csv_escapes_commas_quotes_and_newlines(self):
        csv_text = write_csv(
            ["name", "company"],
            [{"name": 'Ada "A"', "company": "Example,\nInc"}],
        )

        assert '"Ada ""A"""' in csv_text
        assert '"Example,\nInc"' in csv_text
