

import pytest

from tools.taxonomy_builder.pipeline_core.normalize.urls import canonicalize


@pytest.mark.parametrize(
    "base, href, expected",
    [
        # Absolute URL passthrough + strip tracking params
        (
            "https://clutch.co",
            "https://clutch.co/seo?utm_source=x&utm_medium=y&gclid=abc",
            "https://clutch.co/seo",
        ),
        # Relative with leading slash
        (
            "https://clutch.co",
            "/seo",
            "https://clutch.co/seo",
        ),
        # Relative without leading slash (join against base path)
        (
            "https://clutch.co/categories",
            "seo",
            "https://clutch.co/seo",
        ),
        # Preserve non-tracking query params, drop tracking
        (
            "https://clutch.co",
            "/search?q=seo&utm_medium=social",
            "https://clutch.co/search?q=seo",
        ),
        # Drop fragments
        (
            "https://clutch.co/categories",
            "/seo#section",
            "https://clutch.co/seo",
        ),
        # Trim whitespace around href
        (
            "https://clutch.co",
            "   /email-marketing   ",
            "https://clutch.co/email-marketing",
        ),
        # Empty / None href -> empty string
        (
            "https://clutch.co",
            "",
            "",
        ),
        (
            "https://clutch.co",
            None,
            "",
        ),
    ],
)
def test_canonicalize(base, href, expected):
    assert canonicalize(base, href) == expected