"""Evidence view: each [n] citation maps to the passage (and sentence) that supports it."""
from app.evidence import build_evidence, passages_by_source
from app.pipeline import Passage, SearchResult
from conftest import DOCS

P1 = ["Nvidia Corporation is an American technology company. It was founded in 1993 by Jensen Huang, "
      "Chris Malachowsky and Curtis Priem. Nvidia designs GPUs.",
      "Nvidia is headquartered in Santa Clara, California."]
P2 = ["CUDA is a parallel computing platform created by Nvidia in 2006."]


def test_each_citation_gets_supporting_sentence():
    ans = "Nvidia was founded in 1993 by Jensen Huang [1]. It is based in Santa Clara [1]. CUDA came in 2006 [2]."
    ev = build_evidence(ans, {1: P1, 2: P2})
    assert [(e["n"], e["k"]) for e in ev] == [(1, 0), (1, 1), (2, 0)]
    a, b = ev[0]["highlight"]
    assert ev[0]["passage"][a:b].startswith("It was founded in 1993")
    assert "1993" in ev[0]["matched"] and ev[0]["overlap"] > 0.5
    assert "Santa Clara" in ev[1]["passage"]                   # picked the second passage of source 1
    assert ev[2]["claim"] == "CUDA came in 2006."


def test_multiple_citations_on_one_sentence_and_bullets():
    ans = "- **CUDA** was created by Nvidia in 2006 [2][1]."
    ev = build_evidence(ans, {1: P1, 2: P2})
    assert [e["n"] for e in ev] == [2, 1] and ev[0]["claim"] == "CUDA was created by Nvidia in 2006."


def test_no_overlap_or_missing_source():
    ev = build_evidence("Совсем другой текст [1]. Unknown source [7].", {1: P1})
    assert len(ev) == 1 and ev[0]["highlight"] is None and ev[0]["overlap"] == 0


def test_long_passage_is_trimmed_around_highlight():
    long = ("Filler sentence about nothing. " * 60) + "Nvidia was founded in 1993. " + ("More filler here. " * 60)
    ev = build_evidence("Nvidia was founded in 1993 [1].", {1: [long]})[0]
    a, b = ev["highlight"]
    assert len(ev["passage"]) <= 700 and ev["passage"][a:b] == "Nvidia was founded in 1993."
    assert ev["cut_before"] and ev["cut_after"]


def test_passages_by_source_uses_snippet_when_no_passage():
    res = SearchResult(question="q", queries=["q"], sources=DOCS[:2], passages=[Passage(DOCS[1], "CUDA text")])
    out = passages_by_source(res)
    assert out[2] == ["CUDA text"] and "1993" in out[1][0]
