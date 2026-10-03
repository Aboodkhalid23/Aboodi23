import json

import requests

from editor.pipeline.paths import Episode
from editor.pipeline.plan import Beat, EditPlan, load_plan
from editor.pipeline.wikimedia import collect_images, search_commons


def page(title, width, license_, url):
    return {"title": title, "imageinfo": [{
        "url": url, "thumburl": url + "?w=1920", "width": width, "height": width // 2,
        "descriptionurl": "https://commons.wikimedia.org/wiki/" + title,
        "extmetadata": {"LicenseShortName": {"value": license_},
                        "Artist": {"value": "<a href='x'>Jane Doe</a>"}}}]}


class Resp:
    def __init__(self, data=None, content=b"img"):
        self._data, self.content = data, content
        self.status_code, self.headers = 200, {}

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, pages=(), fail=False):
        self.pages, self.fail, self.calls = list(pages), fail, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(url)
        if self.fail:
            raise requests.ConnectionError("blocked")
        if params:  # API search
            return Resp({"query": {"pages": {str(i): p for i, p in enumerate(self.pages)}}} if self.pages else {})
        return Resp(content=b"\xff\xd8jpeg")


PAGES = [page("File:Small.jpg", 800, "CC BY 4.0", "https://u/a.jpg"),
         page("File:Closed.jpg", 2000, "All rights reserved", "https://u/b.jpg"),
         page("File:Good.jpg", 2000, "CC BY-SA 4.0", "https://u/c.jpg")]


def make_plan(n_images=1):
    beats = [Beat(0, 5, "body", "face")]
    for i in range(n_images):
        beats += [Beat(5 + 10 * i, 10 + 10 * i, "body", "image", query="Evergrande",
                       caption="مقر إيفرغراند"),
                  Beat(10 + 10 * i, 15 + 10 * i, "body", "face")]
    return EditPlan({"primary": "vox", "sections": []}, "", [], beats)


def test_filters_small_and_nonfree():
    found = search_commons("Evergrande", session=FakeSession(PAGES))
    assert [i.title for i in found] == ["File:Good.jpg"]
    assert found[0].artist == "Jane Doe"


def test_collect_falls_back_to_text_graphic(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    plan = collect_images(make_plan(), ep, session=FakeSession([]))
    assert plan.beats[1].kind == "graphic"
    assert plan.beats[1].graphic["text"] == "مقر إيفرغراند"  # I-3: Arabic caption, not the query
    assert plan.beats[1].graphic["variant"]                    # and the text card gets a look from the rotation
    assert len(json.loads(ep.fallbacks.read_text())) == 1
    assert load_plan(ep.plan).beats[1].kind == "graphic"


def test_network_error_falls_back(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    plan = collect_images(make_plan(), ep, session=FakeSession(PAGES, fail=True))
    assert plan.beats[1].kind == "graphic"


def test_credits_written(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    plan = collect_images(make_plan(), ep, session=FakeSession(PAGES))
    assert plan.beats[1].kind == "image"
    assert plan.beats[1].treatment == "paper_cutout"
    assert (ep.assets / "img_1.jpg").read_bytes() == b"\xff\xd8jpeg"
    assert "File:Good.jpg — Jane Doe — CC BY-SA 4.0" in ep.credits.read_text()


def test_no_duplicate_images(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    plan = collect_images(make_plan(2), ep, session=FakeSession(PAGES))
    assert [b.kind for b in plan.beats if b.query] == ["image", "graphic"]


class RateLimitedSession(FakeSession):
    """First API call answers 429 with Retry-After, then behaves normally."""
    def __init__(self, pages):
        super().__init__(pages)
        self.limited = True

    def get(self, url, params=None, headers=None, timeout=None):
        if params and self.limited:
            self.limited = False
            r = Resp()
            r.status_code, r.headers = 429, {"Retry-After": "3"}
            return r
        return super().get(url, params, headers, timeout)


def test_search_waits_and_retries_on_429(monkeypatch):
    import editor.pipeline.wikimedia as wm
    waits = []
    monkeypatch.setattr(wm.time, "sleep", waits.append)
    found = search_commons("Evergrande", session=RateLimitedSession(PAGES))
    assert [i.title for i in found] == ["File:Good.jpg"]
    assert 3 in waits


class FirstDownloadRefused(FakeSession):
    """Search works, the first file is rate-limited (429 after retries), the second downloads."""
    def get(self, url, params=None, headers=None, timeout=None):
        if not params and url.startswith("https://u/c"):
            raise requests.HTTPError("429 Too Many Requests")
        return super().get(url, params, headers, timeout)


def test_refused_download_tries_the_next_image(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    pages = PAGES + [page("File:Also.jpg", 2400, "CC0", "https://u/d.jpg")]
    plan = collect_images(make_plan(), ep, session=FirstDownloadRefused(pages))
    assert plan.beats[1].kind == "image"
    assert "File:Also.jpg" in ep.credits.read_text()


def test_entity_credits_are_kept(tmp_path):
    ep = Episode(tmp_path / "ep").ensure()
    (ep.work / "entity_credits.json").write_text(json.dumps({"musk": "Musk.jpg — Gage — CC BY-SA 4.0 — url"}))
    collect_images(make_plan(), ep, session=FakeSession(PAGES))
    assert "Musk.jpg — Gage" in ep.credits.read_text()
