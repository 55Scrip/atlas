from atlas.services.kpi_service import gross_margin, operating_margin, fcf_margin

def test_gross_margin():
    assert gross_margin(50, 100) == 0.5

def test_operating_margin_zero_revenue():
    assert operating_margin(50, 0) is None

def test_fcf_margin_none():
    assert fcf_margin(None, 100) is None
