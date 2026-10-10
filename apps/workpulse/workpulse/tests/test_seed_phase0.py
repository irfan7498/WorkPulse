from workpulse.seed.run import main, wipe


def test_seed_manifest_is_deterministic():
    first = main(seed=42, scale="small")
    second = main(seed=42, scale="small")

    assert first == second
    assert first["seed"] == 42
    assert first["scale"] == "small"
    assert first["counts"]["employees"] == 50
    assert first["counts"]["projects"] == 10
    assert first["counts"]["tasks"] >= 300
    assert "S1" in first["scenarios"]
    assert "S16" in first["scenarios"]


def test_wipe_returns_seed_tagged_doctypes():
    result = wipe()

    assert result["tag"] == "wp_seed"
    assert "Leave Application" in result["doctypes"]
    assert "Task" in result["doctypes"]
