

import pytest

from tools.taxonomy_builder.pipeline_core.normalize.text import clean, slugify


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  SEO  ", "SEO"),
        ("\nSocial\tMedia  Marketing ", "Social Media Marketing"),
        ("", ""),
        (None, ""),
        ("  --  ", "--"),  # clean does not remove punctuation; just trims/normalizes space
        ("Café  &  Crème", "Café & Crème"),
    ],
)
def test_clean(raw, expected):
    assert clean(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("SEO", "seo"),
        ("Social Media Marketing", "social-media-marketing"),
        ("  Email  Marketing  ", "email-marketing"),
        ("PPC/SEM", "ppc-sem"),
        ("Café Crème", "cafe-creme"),  # ascii fold
        ("Ünicode Näme", "unicode-name"),
        ("A   B   C", "a-b-c"),
        ("", ""),
        (None, ""),
        ("---Trim---Dashes---", "trim-dashes"),
    ],
)
def test_slugify(raw, expected):
    assert slugify(raw) == expected