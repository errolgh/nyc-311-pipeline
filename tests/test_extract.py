from datetime import date
import json
from pipeline.extract import build_params, save_to_jsonl

def test_where_clause_has_exclusive_upper_bound():
    params = build_params(
        date(2026, 8, 19),
        "created_date ASC",
        0,
        1000
        )
    assert "2026-08-19" in params["$where"]
    assert "2026-08-20" in params["$where"]

def test_save_to_jsonl_writes_one_json_object_per_line(tmp_path):
    records = [{"id": "1"}, {"id": "2"}]
    path = save_to_jsonl(records, date(2026, 8, 19), base_dir=tmp_path)
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == records[0]
