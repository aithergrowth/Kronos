"""Every annotated example in docs/examples must be read by the detectors the way the trader drew it."""
import pytest

from kronos_trader.examples import EXAMPLES_DIR, check_example, load_examples, report

EXAMPLES = load_examples(EXAMPLES_DIR)


@pytest.mark.skipif(not EXAMPLES, reason="no annotated examples in docs/examples yet")
@pytest.mark.parametrize("example", EXAMPLES, ids=[e.name for e in EXAMPLES])
def test_example_matches_detectors(example):
    result = check_example(example)
    assert result.ok, "\n" + report([result]) + "\n" + "\n".join(result.details)


def test_template_is_ignored_and_loader_handles_synthetic(tmp_path, scenario):
    """The scenario from conftest, written as an example, must pass the checker."""
    scenario.df.to_csv(tmp_path / "scenario.csv", index=False)
    (tmp_path / "scenario.yaml").write_text(
        "symbol: TEST\ntimeframe: 1H\ndirection: bullish\nexpect:\n"
        "  sweep: {candle: '2024-01-01 10:00', level: 100.0}\n"
        "  break: {candle: '2024-01-01 13:00', level: 110.0, kind: BOS}\n"
        "  balance_block: {low: 100.5, high: 102.0}\n"
        "  poi: {low: 100.6, high: 110.0, liquidity: 110.0, protection: 100.6}\n"
        "  tolerance_pips: 1\n", encoding="utf-8")
    (tmp_path / "example_template.yaml").write_text("symbol: X\n", encoding="utf-8")
    examples = load_examples(tmp_path)
    assert [e.name for e in examples] == ["scenario"]
    result = check_example(examples[0])
    assert result.ok, report([result])
    # a wrong annotation is reported, not silently accepted
    (tmp_path / "scenario.yaml").write_text(
        "symbol: TEST\ntimeframe: 1H\ndirection: bullish\nexpect:\n  poi: {low: 95.0, high: 96.0}\n", encoding="utf-8")
    bad = check_example(load_examples(tmp_path)[0])
    assert not bad.ok and "POI" in bad.mismatches[0]
