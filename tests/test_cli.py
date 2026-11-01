from arkhon.cli import main
def test_version(capsys):
    assert main(["version"]) == 0
    assert "ARKHON" in capsys.readouterr().out
def test_doctor():
    assert main(["doctor"]) == 0
