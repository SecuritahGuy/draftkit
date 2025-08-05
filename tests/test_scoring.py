from draftkit.transforms.scoring import ScoringConfig, _score_row

def test_basic_scoring():
    cfg = ScoringConfig()
    row = {
        'passing_yards': 250, 'passing_tds': 2, 'interceptions': 1,
        'rushing_yards': 20, 'rushing_tds': 0,
        'receptions': 5, 'receiving_yards': 60, 'receiving_tds': 1,
        'two_point_conversions': 0, 'fumbles_lost': 0
    }
    pts = _score_row(row, cfg)
    # 250/25=10 + 2*4=8 -2 + 20/10=2 + 5*1=5 + 60/10=6 + 6 = 35
    assert round(pts,2) == 35.0
