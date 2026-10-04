"""Pictures and footage from many libraries, not Wikimedia alone."""
import requests

from editor.pipeline import sources as S


def F(provider, title, width=2000, url=None):
    return S.Found(provider, title, url or f"https://x/{provider}/{title}.jpg", width, 1000, "CC0", "", "", title)


def test_relevance_counts_the_query_words_found():
    assert S.relevance("Evergrande headquarters", "Evergrande Center headquarters Shenzhen") == 1
    assert S.relevance("Evergrande headquarters", "A cat on a sofa") == 0


def test_old_topics_search_the_archives_first():
    assert S.guess_source("oil refinery 1950s", None) == "archive"
    assert S.guess_source("Ottoman empire", None) == "archive"
    assert S.guess_source("Tesla factory", None) == "auto"
    assert S.guess_source("Tesla factory", "stock") == "stock"


def test_best_match_wins_across_libraries_and_broken_ones_are_skipped(monkeypatch):
    def broken(q, s):
        raise requests.ConnectionError("down")
    lib_a = lambda q, s: [F("A", "random street"), F("A", "tiny Evergrande", width=400)]
    lib_b = lambda q, s: [F("B", "Evergrande Center tower")]
    monkeypatch.setitem(S.IMAGE_ORDER, "auto", (broken, lib_a, lib_b))
    errors = []
    found = S.find("Evergrande tower", "image", None, session=object(), errors=errors)
    assert found[0].title == "Evergrande Center tower"          # on-topic beats library order
    assert all(f.width >= S.MIN_IMAGE_WIDTH for f in found)      # too small is never used
    assert errors and "down" in errors[0]


def test_dates_are_dropped_when_a_catalogue_finds_nothing(monkeypatch):
    asked = []
    def lib(q, s):
        asked.append(q)
        return [] if "1950s" in q else [F("LOC", "oil refinery")]
    monkeypatch.setitem(S.IMAGE_ORDER, "archive", (lib,))
    assert S.find("oil refinery 1950s", "image", "archive", session=object())[0].title == "oil refinery"
    assert asked == ["oil refinery 1950s", "oil refinery"]


def test_keyed_libraries_stay_quiet_without_a_key(monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    for f in (S.pexels_images, S.pixabay_images, S.pexels_videos, S.pixabay_videos):
        assert f("city", session=None) == []
