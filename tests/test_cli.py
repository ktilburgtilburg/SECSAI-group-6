from secsai_group_6.cli import main


def test_safe_url_exits_0(capsys):
    assert main(["--check", "https://example.com"]) == 0
    assert "SAFE" in capsys.readouterr().out


def test_threat_exits_1(capsys):
    assert main(["--check", "https://evil.example/login"]) == 1  # stub flags "login"
    assert "MALICIOUS" in capsys.readouterr().out


def test_blank_url_exits_2(capsys):
    assert main(["--check", "   "]) == 2
    assert "error" in capsys.readouterr().err
