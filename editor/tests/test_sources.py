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


class Fake:
    def __init__(self, data):
        self.data = data
    def get(self, url, params=None, headers=None, timeout=None):
        d = self.data
        class R:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return d
        return R()


def test_museum_and_archive_sources_keep_only_free_licences():
    eu = Fake({"items": [{"title": ["Refinery"], "rights": ["http://creativecommons.org/licenses/by/4.0/"], "edmIsShownBy": ["https://e/1.jpg"], "guid": "g"},
                         {"title": ["Closed"], "rights": ["http://creativecommons.org/licenses/by-nc/4.0/"], "edmIsShownBy": ["https://e/2.jpg"]}]})
    assert [f.title for f in S.europeana_images("refinery", eu)] == ["Refinery"]
    wel = Fake({"results": [{"thumbnail": {"url": "https://iiif/x/info.json", "license": {"id": "cc-by-nc"}}, "source": {"title": "a"}},
                            {"thumbnail": {"url": "https://iiif/y/info.json", "license": {"id": "pdm"}}, "source": {"title": "b", "id": "z"}}]})
    got = S.wellcome_images("x", wel)
    assert [f.title for f in got] == ["b"] and got[0].url.endswith("/full/1600,/0/default.jpg")
    art = Fake({"config": {"iiif_url": "https://iiif"}, "data": [{"id": 1, "title": "Mill", "image_id": "abc", "is_public_domain": True,
                                                              "thumbnail": {"width": 3000, "height": 2000}},
                                                             {"id": 2, "title": "Modern", "image_id": "d", "is_public_domain": False}]})
    assert [f.url for f in S.artic_images("mill", art)] == ["https://iiif/abc/full/1686,/0/default.jpg"]


def test_newspaper_searches_old_newspapers_first():
    assert S.IMAGE_ORDER["newspaper"][0] is S.loc_newspapers
    assert S.find("x", "video", "newspaper", session=Fake({}))  == []      # video falls back to the archive order


def test_kits_emoji_codes_and_free_icon_sets_only(monkeypatch):
    from editor.pipeline import kits
    assert kits.emoji_code("🔥") == "1f525" and kits.emoji_code("❤️") == "2764"
    assert kits.icon_svg("someone-paid:logo") is None
    monkeypatch.setattr(kits, "emoji_lottie", lambda c, session=None: None)
    monkeypatch.setattr(kits, "icon_svg", lambda n, session=None: None)
    out = kits.prepare_stickers([{"type": "emoji", "text": "🔥"}, {"type": "icon", "text": "mdi:x", "label": "مصنع"}], str)
    assert [s["type"] for s in out] == ["burst", "stamp"]          # never a broken frame


def test_catalog_lists_every_source_with_its_licence():
    from editor.pipeline.catalog import load, markdown
    d = load()
    assert len(d["sources"]) >= 30 and all(s["licence"] and s["check"].startswith("https://") for s in d["sources"])
    assert "| [Openverse]" in markdown(d) and any(s["use"] == "blocked" for s in d["sources"])
