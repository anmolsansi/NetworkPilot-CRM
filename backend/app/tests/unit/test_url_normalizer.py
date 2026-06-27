import pytest
from app.services.url_normalizer import normalize_linkedin_url, is_valid_linkedin_profile_url, extract_linkedin_slug


class TestNormalizeLinkedinUrl:
    def test_valid_profile_url(self):
        result = normalize_linkedin_url("https://www.linkedin.com/in/johndoe/")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_valid_profile_url_without_www(self):
        result = normalize_linkedin_url("https://linkedin.com/in/johndoe/")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_valid_profile_url_with_query_params(self):
        result = normalize_linkedin_url("https://www.linkedin.com/in/johndoe/?utm_source=x&ref=foo")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_valid_profile_url_with_fragment(self):
        result = normalize_linkedin_url("https://www.linkedin.com/in/johndoe/#section")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_profile_url_with_hyphens_and_underscores(self):
        result = normalize_linkedin_url("https://www.linkedin.com/in/john-doe_123/")
        assert result == ("linkedin.com/in/john-doe_123", "john-doe_123")

    def test_profile_url_lowercase_normalization(self):
        result = normalize_linkedin_url("https://www.linkedin.com/in/JohnDoe/")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_no_protocol(self):
        result = normalize_linkedin_url("www.linkedin.com/in/johndoe/")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_minimal_url(self):
        result = normalize_linkedin_url("linkedin.com/in/johndoe")
        assert result == ("linkedin.com/in/johndoe", "johndoe")

    def test_invalid_company_url(self):
        result = normalize_linkedin_url("https://www.linkedin.com/company/google/")
        assert result is None

    def test_invalid_jobs_url(self):
        result = normalize_linkedin_url("https://www.linkedin.com/jobs/view/123456")
        assert result is None

    def test_invalid_feed_url(self):
        result = normalize_linkedin_url("https://www.linkedin.com/feed/")
        assert result is None

    def test_invalid_search_url(self):
        result = normalize_linkedin_url("https://www.linkedin.com/search/results/people/")
        assert result is None

    def test_invalid_non_linkedin(self):
        result = normalize_linkedin_url("https://www.google.com")
        assert result is None

    def test_empty_string(self):
        result = normalize_linkedin_url("")
        assert result is None

    def test_none(self):
        result = normalize_linkedin_url(None)
        assert result is None

    def test_profile_without_slug(self):
        result = normalize_linkedin_url("https://www.linkedin.com/in/")
        assert result is None


class TestIsValidLinkedinProfileUrl:
    def test_valid(self):
        assert is_valid_linkedin_profile_url("https://www.linkedin.com/in/johndoe/") is True

    def test_invalid(self):
        assert is_valid_linkedin_profile_url("https://www.linkedin.com/company/google/") is False


class TestExtractLinkedinSlug:
    def test_valid(self):
        assert extract_linkedin_slug("https://www.linkedin.com/in/johndoe/") == "johndoe"

    def test_invalid(self):
        assert extract_linkedin_slug("https://www.linkedin.com/company/google/") is None
