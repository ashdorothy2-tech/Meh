import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
from app.money_autopilot import MoneyAutopilot


def test_run_cycle_generates_outputs(tmp_path: pathlib.Path):
    out = tmp_path / "output"
    db = out / "revenue.db"

    bot = MoneyAutopilot(
        db_path=db,
        products_csv=pathlib.Path("data/products.csv"),
        advertisers_json=pathlib.Path("data/advertisers.json"),
        output_dir=out,
    )

    result = bot.run_cycle()

    assert result["affiliate_articles_generated"] == 3
    assert result["sponsorship_emails_generated"] == 5
    assert result["estimated_revenue_this_cycle_usd"] > 0

    pages = list((out / "pages").glob("*.html"))
    outreach = list((out / "outreach").glob("*.txt"))
    assert len(pages) == 3
    assert len(outreach) == 5


def test_cli_prints_json(tmp_path: pathlib.Path, monkeypatch, capsys):
    from app import money_autopilot

    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "out"

    monkeypatch.setattr(
        "sys.argv",
        [
            "money_autopilot.py",
            "--db",
            str(db_path),
            "--products",
            "data/products.csv",
            "--advertisers",
            "data/advertisers.json",
            "--output",
            str(out_path),
        ],
    )

    money_autopilot.main()
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["estimated_revenue_lifetime_usd"] >= payload["estimated_revenue_this_cycle_usd"]
