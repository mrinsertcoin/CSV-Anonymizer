from pathlib import Path

from anonymizer.keymgmt import load_keyfile
from anonymizer.pipeline import run_pipeline
from anonymizer.profile import load_profile


def test_pipeline_e2e(tmp_path):
    root = Path(__file__).resolve().parents[1]
    input_csv = root / "examples" / "customers_raw.csv"
    profile = load_profile(root / "profiles" / "crm-basic-1.0.0.yaml")
    key = load_keyfile(root / "keys" / "key-v1.example.json")
    output_csv = tmp_path / "out.csv"

    stats = run_pipeline(input_csv, output_csv, profile, key.key)

    assert output_csv.exists()
    text = output_csv.read_text(encoding="utf-8")
    assert "max.mustermann@example.com" not in text
    assert "internal_notes" not in text
    assert "PID_" in text
    assert stats.rows_in == 4
    assert stats.rows_out == 4
