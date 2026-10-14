from app.dashboard_routes import clean_site


def test_clean_site_removes_protocol_www_and_slash():
    assert clean_site("https://www.Example.com/") == "example.com"


def test_clean_site_handles_http_and_spaces():
    assert clean_site("  HTTP://example.com  ") == "example.com"


def test_same_site_written_differently_matches():
    assert clean_site("www.example.com") == clean_site("https://example.com/")