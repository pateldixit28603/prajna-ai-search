import json

import pytest
from fastapi.testclient import TestClient

from app import lang as L
from app.main import app
from app.nvidia import NvidiaClient
from app.pipeline import AnswerEngine
from app.store import ThreadStore
from conftest import DOCS, FakeSource, make_settings


@pytest.mark.parametrize("text,code", [
    ("When was Nvidia founded?", "en"),
    ("महात्मा गांधी का जन्म कब हुआ?", "hi"),
    ("Когда была основана компания Nvidia?", "ru"),
    ("متى تأسست شركة إنفيديا؟", "ar"),
    ("英伟达是什么时候成立的？", "zh"),
    ("¿Cuándo se fundó Nvidia?", "es"),
    ("Qué es la computación cuántica y para qué sirve", "es"),
    ("NVIDIA ka CUDA kya hai aur kyun zaroori hai?", "hinglish"),
    ("What is the best GPU for deep learning in 2026?", "en"),
])
def test_detect_language_per_script(text, code):
    assert L.detect_language(text) == code


def test_languages_and_editions():
    assert set(L.LANGUAGES) == {"en", "zh", "hi", "es", "ar", "ru", "hinglish"}
    assert L.LANGUAGES["ar"]["dir"] == "rtl" and all(v["dir"] == "ltr" for k, v in L.LANGUAGES.items() if k != "ar")
    assert L.wiki_edition("ru") == "ru" and L.wiki_edition("zh") == "zh"
    assert L.wiki_edition("en") is None and L.wiki_edition("hinglish") is None and L.wiki_edition(None) is None
    assert L.normalize("AUTO") is None and L.normalize("Ru") == "ru"


def test_restore_citations_keeps_same_sources():
    original = "Nvidia was founded in 1993 [1].\n\nCUDA came in 2006 [2][3]."
    # translation lost [1], renumbered nothing, and invented [7]
    translated = "Nvidia fue fundada en 1993 [7].\n\nCUDA llegó en 2006 [2]."
    out = L.restore_citations(original, translated, n_sources=3)
    paras = out.split("\n\n")
    assert L.citations(paras[0]) == {1: 1} and set(L.citations(paras[1])) == {2, 3}
    assert "[7]" not in out and L.citations_preserved(original, out)
    assert paras[0].endswith("[1].")


def test_restore_citations_paragraph_mismatch_and_rtl_punctuation():
    original = "A [1].\n\nB [2].\n\nC [3]."
    translated = "ألف [1] باء [2] جيم؟"          # merged into one paragraph, lost [3]
    out = L.restore_citations(original, translated, 3)
    assert L.citations_preserved(original, out) and out.endswith("[3]؟")
    assert L.restore_citations(original, "x [1][2][3]", 3) == "x [1][2][3]"


def test_language_instruction():
    assert "Russian" in L.language_instruction("ru")
    assert "Latin" in L.language_instruction("hinglish")
    assert "same language" in L.language_instruction(None)


@pytest.mark.asyncio
async def test_engine_translate_preserves_citations(online_nv, offline_nv):
    s, nv = online_nv
    eng = AnswerEngine(s, nv, {})
    text, ok, _ = await eng.translate("Nvidia was founded in 1993 [1].", "es", 3)
    assert ok and text == "Nvidia fue fundada en 1993 [1]."
    s2, nv2 = offline_nv
    text, ok, msg = await AnswerEngine(s2, nv2, {}).translate("Hello [1].", "ru", 1)
    assert not ok and text == "Hello [1]." and "NVIDIA" in msg


class EditionWiki(FakeSource):
    def __init__(self):
        super().__init__("wikipedia", DOCS)
        self.editions = []

    async def search_edition(self, query, limit, lang):
        self.editions.append((lang, query))
        from app.sources.base import Document
        return [Document(title="Nvidia (ru)", url="https://ru.wikipedia.org/wiki/Nvidia", source="wikipedia",
                         content="Nvidia — американская технологическая компания, основанная в 1993 году " * 3)]


@pytest.mark.asyncio
async def test_native_wikipedia_edition_is_searched(offline_nv):
    s, nv = offline_nv
    wiki = EditionWiki()
    eng = AnswerEngine(s, nv, {"wikipedia": wiki})
    res = await eng.retrieve("Когда была основана Nvidia?", "wiki", [])
    assert wiki.editions == [("ru", "Когда была основана Nvidia?")]
    assert any("ru.wikipedia.org" in d.url for d in res.sources)
    wiki.editions.clear()
    await eng.retrieve("When was Nvidia founded?", "wiki", [], "en")
    assert wiki.editions == []


def _events(resp):
    return [json.loads(l[5:]) for l in resp.text.splitlines() if l.startswith("data:")]


def test_api_language_persisted_and_translate(tmp_path):
    s = make_settings(tmp_path)
    app.state.engine = AnswerEngine(s, NvidiaClient(s), {"wikipedia": FakeSource("wikipedia", DOCS)})
    app.state.store = ThreadStore(tmp_path / "t.db")
    with TestClient(app) as c:
        langs = c.get("/api/health").json()["languages"]
        assert langs["ar"]["dir"] == "rtl" and langs["ru"]["native"] == "Русский"

        ev = _events(c.post("/api/search", json={"query": "When was Nvidia founded?", "focus": "wiki", "lang": "ru"}))
        assert next(e for e in ev if e["type"] == "lang") == {"type": "lang", "lang": "ru", "source": "chosen"}
        tid, turn_id = ev[-1]["thread_id"], ev[-1]["turn_id"]
        assert ev[-1]["meta"]["lang"] == "ru"
        assert c.get(f"/api/threads/{tid}").json()["lang"] == "ru"

        # follow-up without a lang inherits the thread's choice
        ev2 = _events(c.post("/api/search", json={"query": "What is CUDA?", "focus": "wiki", "thread_id": tid}))
        assert next(e for e in ev2 if e["type"] == "lang")["lang"] == "ru"

        # offline: translation degrades gracefully to the original text
        r = c.post("/api/translate", json={"text": "x", "lang": "ar", "turn_id": turn_id, "thread_id": tid}).json()
        assert r["ok"] is False and r["dir"] == "rtl" and r["citations_ok"]
        assert c.post("/api/translate", json={"text": "x", "lang": "klingon"}).status_code == 400


def test_api_translate_online_caches_on_turn(tmp_path, online_nv):
    s, nv = online_nv
    app.state.engine = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", DOCS)})
    app.state.store = store = ThreadStore(tmp_path / "t.db")
    with TestClient(app) as c:
        ev = _events(c.post("/api/search", json={"query": "When was Nvidia founded?", "focus": "wiki"}))
        tid, turn_id = ev[-1]["thread_id"], ev[-1]["turn_id"]
        assert ev[-1]["meta"]["lang"] == "en"
        r = c.post("/api/translate", json={"text": "ignored", "lang": "es", "turn_id": turn_id, "thread_id": tid}).json()
        assert r["ok"] and r["citations_ok"] and "fundada" in r["text"] and "[1]" in r["text"] and "[9]" not in r["text"]
        turn = c.get(f"/api/threads/{tid}").json()["turns"][0]
        assert turn["meta"]["translations"]["es"] == r["text"] and turn["meta"]["shown_lang"] == "es"
        assert store.get_lang(tid) == "es"
