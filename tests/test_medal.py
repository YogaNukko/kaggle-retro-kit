from retrokit.medal import cutoffs


def test_small_competition_uses_percentages():
    c = cutoffs(80)
    assert (c.gold, c.silver, c.bronze) == (8, 16, 32)


def test_mid_competition_fixed_gold():
    c = cutoffs(200)
    assert (c.gold, c.silver, c.bronze) == (10, 40, 80)


def test_large_competition():
    c = cutoffs(1250)
    assert (c.gold, c.silver, c.bronze) == (12, 62, 125)
    assert c.band(5) == "gold" and c.band(62) == "silver" and c.band(100) == "bronze" and c.band(126) == "none"


def test_250_to_999():
    c = cutoffs(500)
    assert (c.gold, c.silver, c.bronze) == (11, 50, 100)
