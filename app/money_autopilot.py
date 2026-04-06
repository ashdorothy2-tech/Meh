from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import html
import json
import pathlib
import random
import sqlite3
import textwrap
import time
import urllib.parse


@dataclasses.dataclass
class Product:
    name: str
    category: str
    description: str
    price_usd: float
    commission_pct: float
    affiliate_url: str


class RevenueDB:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                strategy TEXT NOT NULL,
                details TEXT NOT NULL,
                estimated_revenue_usd REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def record(self, strategy: str, details: str, estimated_revenue_usd: float) -> None:
        self.conn.execute(
            "INSERT INTO events(created_at, strategy, details, estimated_revenue_usd) VALUES (?, ?, ?, ?)",
            (dt.datetime.utcnow().isoformat(), strategy, details, estimated_revenue_usd),
        )
        self.conn.commit()

    def total_estimated_revenue(self) -> float:
        row = self.conn.execute("SELECT COALESCE(SUM(estimated_revenue_usd), 0) FROM events").fetchone()
        return float(row[0]) if row else 0.0


class AffiliateArticleStrategy:
    """Generate affiliate-ready SEO pages from a product feed."""

    def __init__(self, products_csv: pathlib.Path, output_dir: pathlib.Path) -> None:
        self.products_csv = products_csv
        self.output_dir = output_dir

    def _load_products(self) -> list[Product]:
        products: list[Product] = []
        with self.products_csv.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append(
                    Product(
                        name=row["name"],
                        category=row["category"],
                        description=row["description"],
                        price_usd=float(row["price_usd"]),
                        commission_pct=float(row["commission_pct"]),
                        affiliate_url=row["affiliate_url"],
                    )
                )
        return products

    def run(self, max_articles: int = 3) -> tuple[int, float]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        products = sorted(self._load_products(), key=lambda p: p.commission_pct * p.price_usd, reverse=True)
        selected = products[:max_articles]

        total_estimated = 0.0
        generated = 0

        for product in selected:
            slug = urllib.parse.quote_plus(product.name.lower().replace(" ", "-"))
            path = self.output_dir / f"best-{slug}.html"

            expected_sales = random.randint(1, 4)
            estimated = expected_sales * product.price_usd * (product.commission_pct / 100)
            total_estimated += estimated

            body = f"""
            <html><head><title>Best {html.escape(product.name)} Deals</title></head>
            <body>
              <h1>Best {html.escape(product.name)} Deals (Auto-Updated)</h1>
              <p>{html.escape(product.description)}</p>
              <p><strong>Category:</strong> {html.escape(product.category)}</p>
              <p><strong>Price:</strong> ${product.price_usd:.2f}</p>
              <p><a href=\"{html.escape(product.affiliate_url)}\">Buy with our partner link</a></p>
              <hr />
              <p>Monetization layer: add your ad network script in this template.</p>
            </body></html>
            """
            path.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
            generated += 1

        return generated, total_estimated


class SponsorshipEmailStrategy:
    """Create cold-outreach emails for newsletter sponsorship inventory."""

    def __init__(self, advertisers_json: pathlib.Path, output_dir: pathlib.Path) -> None:
        self.advertisers_json = advertisers_json
        self.output_dir = output_dir

    def run(self, max_emails: int = 5) -> tuple[int, float]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        advertisers = json.loads(self.advertisers_json.read_text(encoding="utf-8"))["advertisers"]
        advertisers = advertisers[:max_emails]

        total_estimated = 0.0
        generated = 0
        today = dt.date.today().isoformat()

        for ad in advertisers:
            filename = f"pitch-{ad['company'].lower().replace(' ', '-')}.txt"
            path = self.output_dir / filename
            rate = float(ad["typical_sponsorship_usd"])
            close_probability = 0.08
            estimated = rate * close_probability
            total_estimated += estimated

            email = f"""Subject: Sponsorship slot available for {ad['company']}

Hi {ad['contact_name']},

I run an automated niche content publication that ranks for buyer-intent searches.
We have sponsorship inventory opening in the next issue ({today}) and your product is a fit.

Package:
- 1 dedicated section
- 1 permanent affiliate recommendation page
- 1 follow-up mention

Rate card: ${rate:,.0f}
If interested, reply with 'yes' and your preferred billing method.

Best,
AutoMonetize Agent
"""
            path.write_text(email, encoding="utf-8")
            generated += 1

        return generated, total_estimated


class MoneyAutopilot:
    def __init__(self, db_path: pathlib.Path, products_csv: pathlib.Path, advertisers_json: pathlib.Path, output_dir: pathlib.Path) -> None:
        self.db = RevenueDB(db_path)
        self.affiliate = AffiliateArticleStrategy(products_csv, output_dir / "pages")
        self.sponsor = SponsorshipEmailStrategy(advertisers_json, output_dir / "outreach")

    def run_cycle(self) -> dict[str, float | int]:
        a_count, a_est = self.affiliate.run()
        self.db.record("affiliate_articles", f"generated={a_count}", a_est)

        s_count, s_est = self.sponsor.run()
        self.db.record("sponsorship_outreach", f"generated={s_count}", s_est)

        total = self.db.total_estimated_revenue()
        return {
            "affiliate_articles_generated": a_count,
            "sponsorship_emails_generated": s_count,
            "estimated_revenue_this_cycle_usd": round(a_est + s_est, 2),
            "estimated_revenue_lifetime_usd": round(total, 2),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a mostly hands-off monetization automation loop.")
    parser.add_argument("--db", default="output/revenue.db", help="Path to sqlite database")
    parser.add_argument("--products", default="data/products.csv", help="CSV feed with affiliate products")
    parser.add_argument("--advertisers", default="data/advertisers.json", help="JSON list of target advertisers")
    parser.add_argument("--output", default="output", help="Output folder")
    parser.add_argument("--interval-minutes", type=int, default=0, help="If >0, run forever on this interval")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bot = MoneyAutopilot(
        db_path=pathlib.Path(args.db),
        products_csv=pathlib.Path(args.products),
        advertisers_json=pathlib.Path(args.advertisers),
        output_dir=pathlib.Path(args.output),
    )

    while True:
        result = bot.run_cycle()
        print(json.dumps(result, indent=2))

        if args.interval_minutes <= 0:
            break
        time.sleep(args.interval_minutes * 60)


if __name__ == "__main__":
    main()
