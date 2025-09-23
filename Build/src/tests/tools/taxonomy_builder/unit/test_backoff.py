import types
import pytest

from tools.taxonomy_builder.pipeline_core.fetch.backoff import should_retry, next_sleep
import tools.taxonomy_builder.pipeline_core.fetch.backoff as backoff_mod


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_should_retry_true(status):
    assert should_retry(status) is True


@pytest.mark.parametrize("status", [200, 201, 204, 301, 304, 404])
def test_should_retry_false(status):
    assert should_retry(status) is False


def test_next_sleep_non_negative():
    # With default jitter, all sleeps should be >= 0 and reasonably bounded
    vals = [next_sleep(i) for i in range(6)]
    assert all(v >= 0 for v in vals)
    # Should not explode to infinity; allow a generous cap in case defaults changed
    assert max(vals) <= 120.0


def test_next_sleep_monotonic_with_deterministic_jitter(monkeypatch):
    """Force jitter to a deterministic value so growth with retry is testable.

    We monkeypatch the module's `random` object used by backoff to return the
    midpoint for uniform(a, b) and a fixed 0.5 for random(). This makes the
    exponential component the dominant factor and should yield non-decreasing
    sleeps as retry increases, up to the cap where values may plateau.
    """
    fake_random = types.SimpleNamespace(
        random=lambda: 0.5,
        uniform=lambda a, b: (a + b) / 2.0,
    )
    monkeypatch.setattr(backoff_mod, "random", fake_random, raising=True)

    seq = [next_sleep(i) for i in range(8)]

    # Non-decreasing sequence (can plateau at cap)
    for i in range(len(seq) - 1):
        assert seq[i + 1] >= seq[i]

    # Cap sanity: if the function supports `cap`, ensure we can cap at a small value
    try:
        capped = [next_sleep(i, cap=2.0) for i in range(8)]
        assert max(capped) <= 2.0 + 1e-9
    except TypeError:
        # If signature doesn't accept cap, skip this portion
        pytest.skip("next_sleep does not accept 'cap' parameter in this build")


def test_next_sleep_responds_to_retry_with_custom_base(monkeypatch):
    """If next_sleep accepts `base`, smaller base should yield smaller sleeps.
    We make jitter deterministic to compare magnitudes.
    """
    fake_random = types.SimpleNamespace(
        random=lambda: 0.5,
        uniform=lambda a, b: (a + b) / 2.0,
    )
    monkeypatch.setattr(backoff_mod, "random", fake_random, raising=True)

    try:
        low_base = [next_sleep(i, base=0.25, cap=10.0) for i in range(5)]
        high_base = [next_sleep(i, base=1.0, cap=10.0) for i in range(5)]
        assert sum(low_base) < sum(high_base)
    except TypeError:
        pytest.skip("next_sleep does not accept 'base' parameter in this build")
