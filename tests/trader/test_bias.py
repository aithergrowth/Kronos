from kronos_trader.config import BiasParams
from kronos_trader.core import Bias, CandleSeries, Timeframe, TradeMode
from kronos_trader.strategy import analyze_structure, combine_biases, timeframe_bias

T = Timeframe


def test_liquidity_and_balance_aligned_is_bullish(scenario):
    tb = timeframe_bias(analyze_structure(scenario))
    assert tb.liquidity_view is Bias.BULLISH and tb.balance_view is Bias.BULLISH and tb.bias is Bias.BULLISH
    assert tb.timeframe is T.H_1


def test_conflicting_views_are_fifty_fifty(scenario_rows):
    rows = list(scenario_rows) + [
        (112.5, 113, 111, 112),      # 16
        (112, 112.5, 110.5, 111),    # 17 -> swing high 113 at idx 15 confirmed
        (111, 113.5, 110.8, 112),    # 18 wick above 113, body inside -> buy-side sweep
    ]
    st = analyze_structure(CandleSeries.from_records(rows, T.H_1))
    tb = timeframe_bias(st)
    assert tb.liquidity_view is Bias.BEARISH   # buy-side liquidity taken
    assert tb.balance_view is Bias.BULLISH     # structure still bullish
    assert tb.bias is Bias.NEUTRAL
    # conflict_rule "recent": the sweep (the last candle) is more recent than the gap that carries the balance view
    recent = timeframe_bias(st, BiasParams(conflict_rule="recent"))
    assert recent.bias is Bias.BEARISH and "more recent" in recent.notes[-1]


def test_p_break_flips_the_balance_view(scenario_rows):
    rows = list(scenario_rows) + [       # a three-candle decline with overlapping ranges: no new gap forms
        (112.5, 113, 109, 109.5),    # 16
        (109.5, 111, 106.5, 107),    # 17
        (107, 109.5, 104, 104.2),    # 18 closes below 105 = low of P (candle 13) of the last gap -> P breaks
    ]
    st = analyze_structure(CandleSeries.from_records(rows, T.H_1))
    assert st.last_gap.index == 14 and st.last_gap.violated_index == 18
    assert timeframe_bias(st).balance_view is Bias.BEARISH                                   # continuation
    assert timeframe_bias(st, BiasParams(balance_violation="neutral")).balance_view is Bias.NEUTRAL


def test_m_d_4h_combination_is_on_by_default():
    votes = {T.MN_1: Bias.BULLISH, T.W_1: Bias.NEUTRAL, T.D_1: Bias.BULLISH, T.H_4: Bias.BULLISH, T.H_1: Bias.NEUTRAL}
    assert combine_biases(votes).mode is TradeMode.FULL                                        # D 01:05-01:43
    assert combine_biases(votes, BiasParams(extra_combos_enabled=False)).mode is TradeMode.NONE  # K1 slide only


def test_stale_liquidity_event_is_neutral(scenario):
    tb = timeframe_bias(analyze_structure(scenario), BiasParams(liquidity_lookback=1))
    assert tb.liquidity_view is Bias.NEUTRAL and tb.bias is Bias.NEUTRAL


def test_no_structure_is_neutral():
    flat = CandleSeries.from_records([(1, 1.1, 0.9, 1)] * 10, T.D_1)
    tb = timeframe_bias(analyze_structure(flat))
    assert tb.bias is Bias.NEUTRAL


def test_valid_full_combinations():
    for combo in [(T.MN_1, T.W_1, T.D_1), (T.W_1, T.D_1, T.H_4), (T.MN_1, T.D_1, T.H_1)]:
        biases = {tf: (Bias.BULLISH if tf in combo else Bias.NEUTRAL) for tf in [T.MN_1, T.W_1, T.D_1, T.H_4, T.H_1]}
        d = combine_biases(biases)
        assert d.mode is TradeMode.FULL and d.direction is Bias.BULLISH and d.matched_combo == combo and d.tradable


def test_scalp_only_combination():
    d = combine_biases({T.MN_1: Bias.NEUTRAL, T.W_1: Bias.BULLISH, T.D_1: Bias.BEARISH, T.H_4: Bias.BEARISH, T.H_1: Bias.BEARISH})
    assert d.mode is TradeMode.SCALP and d.direction is Bias.BEARISH
    assert d.conflicting == (T.W_1,)


def test_invalid_combination_and_too_few_votes():
    d = combine_biases({T.MN_1: Bias.BULLISH, T.W_1: Bias.BULLISH, T.D_1: Bias.NEUTRAL, T.H_4: Bias.BULLISH, T.H_1: Bias.NEUTRAL})
    assert d.mode is TradeMode.NONE and not d.tradable and "not a valid combination" in d.reason
    d = combine_biases({T.MN_1: Bias.BULLISH, T.W_1: Bias.BULLISH, T.D_1: Bias.NEUTRAL, T.H_4: Bias.NEUTRAL, T.H_1: Bias.BEARISH})
    assert d.mode is TradeMode.NONE and d.direction is Bias.NEUTRAL


def test_four_of_five_still_matches_a_combo_and_opposing_votes_allowed():
    d = combine_biases({T.MN_1: Bias.BEARISH, T.W_1: Bias.BEARISH, T.D_1: Bias.BEARISH, T.H_4: Bias.BULLISH, T.H_1: Bias.BULLISH})
    assert d.mode is TradeMode.FULL and d.direction is Bias.BEARISH and d.conflicting == (T.H_4, T.H_1)


def test_required_aligned_blocks_a_match_without_that_timeframe():
    """``bias.required_aligned`` names timeframes that must be among the aligned ones; a 3-of-5 match without them is refused."""
    from kronos_trader.config import BiasParams
    from kronos_trader.core import Bias, TradeMode
    from kronos_trader.core.timeframe import Timeframe as T
    from kronos_trader.strategy.bias import combine_biases
    readings = {T.MN_1: Bias.BULLISH, T.W_1: Bias.BULLISH, T.D_1: Bias.BULLISH, T.H_4: Bias.NEUTRAL, T.H_1: Bias.NEUTRAL}
    assert combine_biases(readings, BiasParams()).mode is TradeMode.FULL
    blocked = combine_biases(readings, BiasParams(required_aligned=(T.H_1,)))
    assert blocked.mode is TradeMode.NONE and "1H not aligned (required)" in blocked.reason
    readings[T.H_1] = Bias.BULLISH
    assert combine_biases(readings, BiasParams(required_aligned=(T.H_1,))).mode is TradeMode.FULL


def test_no_trade_against_vetoes_a_match_the_monthly_reads_the_other_way():
    """``bias.no_trade_against``: a timeframe in that list that reads the opposite direction turns a match into no trade
    (loss anatomy, 4 October: gold shorts against a bullish monthly 38 %, -8.6R). Off by default."""
    votes = {T.MN_1: Bias.BULLISH, T.W_1: Bias.NEUTRAL, T.D_1: Bias.BEARISH, T.H_4: Bias.BEARISH, T.H_1: Bias.BEARISH}
    assert combine_biases(votes).mode is TradeMode.SCALP
    d = combine_biases(votes, BiasParams(no_trade_against=(T.MN_1,)))
    assert d.mode is TradeMode.NONE and d.direction is Bias.NEUTRAL and "1M against" in d.reason
    assert combine_biases(votes, BiasParams(no_trade_against=(T.W_1,))).mode is TradeMode.SCALP   # neutral is not against


def test_scalp_enabled_false_drops_the_scalp_combination():
    votes = {T.MN_1: Bias.NEUTRAL, T.W_1: Bias.NEUTRAL, T.D_1: Bias.BEARISH, T.H_4: Bias.BEARISH, T.H_1: Bias.BEARISH}
    assert combine_biases(votes).mode is TradeMode.SCALP
    d = combine_biases(votes, BiasParams(scalp_enabled=False))
    assert d.mode is TradeMode.NONE and "not a valid combination" in d.reason



def test_a_break_taken_back_by_the_next_close_reads_as_a_sweep(scenario_rows):
    """``bias.reclaim_candles``: a break whose level a close takes back within that many candles is a sweep of the level
    in the liquidity view (his gold long of 18 Sep 2025: the 1H closed under the FOMC low and the next hour back above
    it). Off by default: the break decides."""
    rows = list(scenario_rows[:14]) + [(110.8, 111, 109, 109.5)]    # 14: closes back under 110, broken up at 13
    st = analyze_structure(CandleSeries.from_records(rows, T.H_1))
    assert st.last_break.index == 13 and st.last_break.direction is Bias.BULLISH
    assert timeframe_bias(st).liquidity_view is Bias.BULLISH
    taken = timeframe_bias(st, BiasParams(reclaim_candles=1))
    assert taken.liquidity_view is Bias.BEARISH and "taken back" in taken.notes[0]

    later = list(scenario_rows[:14]) + [(110.8, 112, 110.2, 111.5), (111.5, 111.8, 109, 109.4)]   # back under 110 at 15
    st = analyze_structure(CandleSeries.from_records(later, T.H_1))
    assert timeframe_bias(st, BiasParams(reclaim_candles=1)).liquidity_view is Bias.BULLISH
    assert timeframe_bias(st, BiasParams(reclaim_candles=2)).liquidity_view is Bias.BEARISH


def test_a_close_beyond_the_last_gap_flips_the_balance_view_when_asked(scenario_rows):
    """``bias.shift_flips_balance``: a close beyond the far edge of the last gap (the balance shift the confirmation
    trades) turns the balance view before its P breaks. Off by default: the gap holds until P is closed through."""
    rows = list(scenario_rows) + [
        (112.5, 112.8, 108, 108.5),   # 16
        (108.5, 111.5, 105.5, 105.8),  # 17 closes under 106 (the low of the gap 106-110) but above 105 (the low of its P)
    ]
    st = analyze_structure(CandleSeries.from_records(rows, T.H_1))
    gap = st.last_gap
    assert (gap.low, gap.high, gap.index) == (106, 110, 14) and not gap.is_violated
    assert timeframe_bias(st).balance_view is Bias.BULLISH
    shifted = timeframe_bias(st, BiasParams(shift_flips_balance=True))
    assert shifted.balance_view is Bias.BEARISH and "balance shift" in shifted.notes[1]


def test_a_refused_direction_does_not_hide_a_match_the_other_way():
    """8 October: with ``min_matching_timeframes`` 2 the bullish month and 4H, vetoed by the weekly, returned before the
    bearish W+D+1H was looked at, so EURUSD shorts were refused; the mirror image (a bearish month and 4H) traded."""
    from kronos_trader.config import BiasParams
    params = BiasParams(min_matching_timeframes=2, required_aligned=(T.H_1,), no_trade_against=(T.W_1,),
                        full_combos=((T.MN_1, T.W_1, T.D_1), (T.MN_1, T.D_1, T.H_1), (T.D_1, T.H_1)))
    votes = {T.MN_1: Bias.BULLISH, T.W_1: Bias.BEARISH, T.D_1: Bias.BEARISH, T.H_4: Bias.BULLISH, T.H_1: Bias.BEARISH}
    d = combine_biases(votes, params)
    assert d.mode is TradeMode.FULL and d.direction is Bias.BEARISH and d.matched_combo == (T.D_1, T.H_1)
    mirror = {tf: (b.opposite if b is not Bias.NEUTRAL else b) for tf, b in votes.items()}
    m = combine_biases(mirror, params)
    assert m.mode is TradeMode.FULL and m.direction is Bias.BULLISH and m.matched_combo == (T.D_1, T.H_1)
    # the 1H requirement refused the bullish month and 4H first; the bearish D+1H still trades
    votes = {T.MN_1: Bias.BULLISH, T.W_1: Bias.NEUTRAL, T.D_1: Bias.BEARISH, T.H_4: Bias.BULLISH, T.H_1: Bias.BEARISH}
    assert combine_biases(votes, params).direction is Bias.BEARISH
    # a weekly against the bearish side still vetoes it, whatever refused the bullish side
    votes = {T.MN_1: Bias.BULLISH, T.W_1: Bias.BULLISH, T.D_1: Bias.BEARISH, T.H_4: Bias.NEUTRAL, T.H_1: Bias.BEARISH}
    assert combine_biases(votes, params).mode is TradeMode.NONE
    # when neither direction matches, the refusal is still the reason
    votes = {T.MN_1: Bias.BULLISH, T.W_1: Bias.BEARISH, T.D_1: Bias.BEARISH, T.H_4: Bias.BULLISH, T.H_1: Bias.NEUTRAL}
    none = combine_biases(votes, params)
    assert none.mode is TradeMode.NONE and none.direction is Bias.NEUTRAL and "1W against" in none.reason
