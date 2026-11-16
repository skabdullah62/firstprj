"""
Smart Inventory Management for Event Enterprises
-------------------------------------------------
A simple working mini-project built with only Python standard libraries.
Run:
    python app.py
Open:
    http://127.0.0.1:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparseewwww
import sqlite3
import html
from datetime import datetime

DB_NAME = "smart_inventory.db"
HOST = "127.0.0.1"
PORT = 8000


def connect_db():
    return sqlite3.connect(DB_NAME)


def init_db():
    """Create database tables and seed sample data when the database is empty."""
    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            total_qty INTEGER NOT NULL,
            available_qty INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL,
            unit_cost REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            client_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            venue TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Allocated',
            allocated_at TEXT NOT NULL,
            returned_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            qty INTEGER NOT NULL,
            remarks TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """)

    cur.execute("SELECT COUNT(*) FROM items")
    if cur.fetchone()[0] == 0:
        sample_items = [
            ("Banquet Chair", "Furniture", 500, 420, 60, 650),
            ("Round Dining Table", "Furniture", 120, 90, 15, 3200),
            ("LED Par Light", "Lighting", 80, 55, 10, 2400),
            ("Wireless Microphone", "Audio", 30, 22, 5, 4500),
            ("Decor Flower Stand", "Decoration", 150, 125, 20, 850),
        ]
        cur.executemany("""
            INSERT INTO items(name, category, total_qty, available_qty, reorder_level, unit_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_items)

        sample_events = [
            ("Corporate Annual Meet", "Apex Solutions", "2026-07-10", "Deccan Convention Hall"),
            ("Wedding Reception", "Khan Family", "2026-07-18", "Pearl Banquets"),
        ]
        cur.executemany("""
            INSERT INTO events(event_name, client_name, event_date, venue)
            VALUES (?, ?, ?, ?)
        """, sample_events)

    con.commit()
    con.close()


def query_all(sql, params=()):
    con = connect_db()
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, params).fetchall()
    con.close()
    return rows


def execute(sql, params=()):
    con = connect_db()
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    last_id = cur.lastrowid
    con.close()
    return last_id


def esc(value):
    return html.escape(str(value))


def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f7fb; color: #172033; }}
    header {{ background: linear-gradient(120deg, #0b2c54, #1565c0); color: white; padding: 28px 42px; }}
    header h1 {{ margin: 0; font-size: 28px; }}
    header p {{ margin: 8px 0 0; opacity: 0.9; }}
    nav {{ background: white; padding: 12px 42px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
    nav a {{ color: #0b2c54; text-decoration: none; margin-right: 22px; font-weight: 700; }}
    main {{ padding: 28px 42px; max-width: 1180px; margin: auto; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; }}
    .card {{ background: white; border-radius: 18px; padding: 20px; box-shadow: 0 8px 25px rgba(14, 42, 84, 0.08); }}
    .card h2, .card h3 {{ margin-top: 0; color: #0b2c54; }}
    .metric {{ font-size: 34px; font-weight: 800; color: #1565c0; margin: 8px 0; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 16px; overflow: hidden; }}
    th {{ background: #0b2c54; color: white; text-align: left; }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid #eef1f6; }}
    tr:hover {{ background: #f9fbff; }}
    input, select {{ width: 100%; padding: 11px; margin: 7px 0 14px; border: 1px solid #cad4e1; border-radius: 10px; }}
    label {{ font-weight: 700; color: #34445e; }}
    button {{ background: #1565c0; color: white; border: none; padding: 11px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; }}
    button:hover {{ background: #0b2c54; }}
    .danger {{ color: #c62828; font-weight: 700; }}
    .ok {{ color: #2e7d32; font-weight: 700; }}
    .warning {{ background: #fff7e0; color: #7a4a00; padding: 10px 12px; border-radius: 10px; margin-bottom: 14px; }}
    .success {{ background: #e8f5e9; color: #1b5e20; padding: 10px 12px; border-radius: 10px; margin-bottom: 14px; }}
    .row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; }}
    footer {{ text-align: center; color: #73829a; padding: 18px; }}
</style>
</head>
<body>
<header>
    <h1>Smart Inventory Management for Event Enterprises</h1>
    <p>Track stock, allocate items to events, monitor low inventory, and manage returns.</p>
</header>
<nav>
    <a href="/">Dashboard</a>
    <a href="/items">Inventory</a>
    <a href="/events">Events</a>
    <a href="/allocate">Allocate</a>
    <a href="/transactions">Transactions</a>
</nav>
<main>{body}</main>
<footer>Mini Project Demo | Python + SQLite</footer>
</body>
</html>"""


class SmartInventoryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            self.render_dashboard()
        elif route == "/items":
            self.render_items()
        elif route == "/events":
            self.render_events()
        elif route == "/allocate":
            self.render_allocate()
        elif route == "/transactions":
            self.render_transactions()
        else:
            self.send_html(page("Not Found", "<div class='card'><h2>404 - Page not found</h2></div>"), 404)

    def do_POST(self):
        route = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length).decode("utf-8")
        form = {k: v[0] for k, v in parse_qs(data).items()}

        try:
            if route == "/items/add":
                self.add_item(form)
            elif route == "/events/add":
                self.add_event(form)
            elif route == "/allocate/add":
                self.allocate_item(form)
            elif route == "/return":
                self.return_item(form)
            else:
                self.redirect("/")
        except Exception as exc:
            self.send_html(page("Error", f"<div class='card'><h2>Error</h2><p class='danger'>{esc(exc)}</p><a href='/'>Back</a></div>"), 500)

    def send_html(self, content, status=200):
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def render_dashboard(self):
        stats = query_all("""
            SELECT
                COUNT(*) AS total_items,
                SUM(total_qty) AS total_stock,
                SUM(available_qty) AS available_stock,
                SUM(CASE WHEN available_qty <= reorder_level THEN 1 ELSE 0 END) AS low_stock
            FROM items
        """)[0]
        events = query_all("SELECT COUNT(*) AS total_events FROM events")[0]["total_events"]
        recent = query_all("""
            SELECT t.created_at, i.name, t.action, t.qty, t.remarks
            FROM transactions t JOIN items i ON i.id = t.item_id
            ORDER BY t.id DESC LIMIT 5
        """)
        low_items = query_all("SELECT name, available_qty, reorder_level FROM items WHERE available_qty <= reorder_level")

        recent_rows = "".join(
            f"<tr><td>{esc(r['created_at'])}</td><td>{esc(r['name'])}</td><td>{esc(r['action'])}</td><td>{esc(r['qty'])}</td><td>{esc(r['remarks'])}</td></tr>"
            for r in recent
        ) or "<tr><td colspan='5'>No transactions yet.</td></tr>"
        low_list = "".join(f"<li>{esc(r['name'])}: {esc(r['available_qty'])} left, reorder at {esc(r['reorder_level'])}</li>" for r in low_items) or "<li>All items are above reorder level.</li>"

        body = f"""
        <section class="grid">
            <div class="card"><h3>Total Item Types</h3><div class="metric">{stats['total_items'] or 0}</div></div>
            <div class="card"><h3>Total Stock Units</h3><div class="metric">{stats['total_stock'] or 0}</div></div>
            <div class="card"><h3>Available Units</h3><div class="metric">{stats['available_stock'] or 0}</div></div>
            <div class="card"><h3>Active Events</h3><div class="metric">{events}</div></div>
        </section>
        <br>
        <section class="card">
            <h2>Low Stock Alerts</h2>
            <ul>{low_list}</ul>
        </section>
        <br>
        <section class="card">
            <h2>Recent Transactions</h2>
            <table><tr><th>Date</th><th>Item</th><th>Action</th><th>Qty</th><th>Remarks</th></tr>{recent_rows}</table>
        </section>
        """
        self.send_html(page("Dashboard", body))

    def render_items(self):
        rows = query_all("SELECT * FROM items ORDER BY category, name")
        item_rows = "".join(
            f"<tr><td>{r['id']}</td><td>{esc(r['name'])}</td><td>{esc(r['category'])}</td><td>{r['total_qty']}</td><td>{r['available_qty']}</td><td>{r['reorder_level']}</td><td>₹{r['unit_cost']:.2f}</td><td>{'<span class=danger>Low</span>' if r['available_qty'] <= r['reorder_level'] else '<span class=ok>OK</span>'}</td></tr>"
            for r in rows
        )
        body = f"""
        <div class="row">
            <section class="card">
                <h2>Add Inventory Item</h2>
                <form method="post" action="/items/add">
                    <label>Item Name</label><input name="name" required>
                    <label>Category</label><input name="category" required>
                    <label>Total Quantity</label><input name="total_qty" type="number" min="1" required>
                    <label>Reorder Level</label><input name="reorder_level" type="number" min="0" required>
                    <label>Unit Cost</label><input name="unit_cost" type="number" min="0" step="0.01" required>
                    <button>Add Item</button>
                </form>
            </section>
            <section class="card">
                <h2>Inventory List</h2>
                <table><tr><th>ID</th><th>Name</th><th>Category</th><th>Total</th><th>Available</th><th>Reorder</th><th>Cost</th><th>Status</th></tr>{item_rows}</table>
            </section>
        </div>
        """
        self.send_html(page("Inventory", body))

    def render_events(self):
        rows = query_all("SELECT * FROM events ORDER BY event_date")
        event_rows = "".join(
            f"<tr><td>{r['id']}</td><td>{esc(r['event_name'])}</td><td>{esc(r['client_name'])}</td><td>{esc(r['event_date'])}</td><td>{esc(r['venue'])}</td></tr>"
            for r in rows
        )
        body = f"""
        <div class="row">
            <section class="card">
                <h2>Create Event</h2>
                <form method="post" action="/events/add">
                    <label>Event Name</label><input name="event_name" required>
                    <label>Client Name</label><input name="client_name" required>
                    <label>Event Date</label><input name="event_date" type="date" required>
                    <label>Venue</label><input name="venue" required>
                    <button>Create Event</button>
                </form>
            </section>
            <section class="card">
                <h2>Event Schedule</h2>
                <table><tr><th>ID</th><th>Event</th><th>Client</th><th>Date</th><th>Venue</th></tr>{event_rows}</table>
            </section>
        </div>
        """
        self.send_html(page("Events", body))

    def render_allocate(self, message=""):
        events = query_all("SELECT id, event_name, event_date FROM events ORDER BY event_date")
        items = query_all("SELECT id, name, available_qty FROM items ORDER BY name")
        allocations = query_all("""
            SELECT a.id, e.event_name, i.name, a.qty, a.status, a.allocated_at
            FROM allocations a
            JOIN events e ON e.id = a.event_id
            JOIN items i ON i.id = a.item_id
            ORDER BY a.id DESC
        """)
        event_options = "".join(f"<option value='{e['id']}'>{esc(e['event_name'])} - {esc(e['event_date'])}</option>" for e in events)
        item_options = "".join(f"<option value='{i['id']}'>{esc(i['name'])} ({i['available_qty']} available)</option>" for i in items)
        allocation_rows = "".join(
            f"<tr><td>{a['id']}</td><td>{esc(a['event_name'])}</td><td>{esc(a['name'])}</td><td>{a['qty']}</td><td>{esc(a['status'])}</td><td>{esc(a['allocated_at'])}</td><td>{self.return_button(a)}</td></tr>"
            for a in allocations
        ) or "<tr><td colspan='7'>No allocations yet.</td></tr>"
        msg_html = f"<div class='success'>{esc(message)}</div>" if message else ""
        body = f"""
        {msg_html}
        <div class="row">
            <section class="card">
                <h2>Allocate Stock to Event</h2>
                <form method="post" action="/allocate/add">
                    <label>Select Event</label><select name="event_id" required>{event_options}</select>
                    <label>Select Item</label><select name="item_id" required>{item_options}</select>
                    <label>Quantity Required</label><input name="qty" type="number" min="1" required>
                    <button>Allocate Item</button>
                </form>
            </section>
            <section class="card">
                <h2>Allocation Register</h2>
                <table><tr><th>ID</th><th>Event</th><th>Item</th><th>Qty</th><th>Status</th><th>Allocated At</th><th>Action</th></tr>{allocation_rows}</table>
            </section>
        </div>
        """
        self.send_html(page("Allocate", body))

    def return_button(self, allocation):
        if allocation["status"] == "Returned":
            return "<span class='ok'>Completed</span>"
        return f"""
        <form method="post" action="/return" style="margin:0">
            <input type="hidden" name="allocation_id" value="{allocation['id']}">
            <button>Return</button>
        </form>"""

    def render_transactions(self):
        rows = query_all("""
            SELECT t.id, t.created_at, i.name, t.action, t.qty, t.remarks
            FROM transactions t JOIN items i ON i.id = t.item_id
            ORDER BY t.id DESC
        """)
        tx_rows = "".join(
            f"<tr><td>{r['id']}</td><td>{esc(r['created_at'])}</td><td>{esc(r['name'])}</td><td>{esc(r['action'])}</td><td>{r['qty']}</td><td>{esc(r['remarks'])}</td></tr>"
            for r in rows
        ) or "<tr><td colspan='6'>No transactions available.</td></tr>"
        body = f"""
        <section class="card">
            <h2>Inventory Transaction Log</h2>
            <table><tr><th>ID</th><th>Date</th><th>Item</th><th>Action</th><th>Qty</th><th>Remarks</th></tr>{tx_rows}</table>
        </section>
        """
        self.send_html(page("Transactions", body))

    def add_item(self, form):
        name = form["name"].strip()
        category = form["category"].strip()
        total_qty = int(form["total_qty"])
        reorder_level = int(form["reorder_level"])
        unit_cost = float(form["unit_cost"])
        item_id = execute("""
            INSERT INTO items(name, category, total_qty, available_qty, reorder_level, unit_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, total_qty, total_qty, reorder_level, unit_cost))
        execute("""
            INSERT INTO transactions(item_id, action, qty, remarks, created_at)
            VALUES (?, 'Stock Added', ?, 'New inventory item created', ?)
        """, (item_id, total_qty, now()))
        self.redirect("/items")

    def add_event(self, form):
        execute("""
            INSERT INTO events(event_name, client_name, event_date, venue)
            VALUES (?, ?, ?, ?)
        """, (form["event_name"].strip(), form["client_name"].strip(), form["event_date"], form["venue"].strip()))
        self.redirect("/events")

    def allocate_item(self, form):
        event_id = int(form["event_id"])
        item_id = int(form["item_id"])
        qty = int(form["qty"])
        item = query_all("SELECT name, available_qty FROM items WHERE id=?", (item_id,))[0]
        if qty > item["available_qty"]:
            raise ValueError(f"Only {item['available_qty']} units of {item['name']} are available. Allocation cannot be completed.")

        execute("""
            INSERT INTO allocations(event_id, item_id, qty, status, allocated_at)
            VALUES (?, ?, ?, 'Allocated', ?)
        """, (event_id, item_id, qty, now()))
        execute("UPDATE items SET available_qty = available_qty - ? WHERE id = ?", (qty, item_id))
        execute("""
            INSERT INTO transactions(item_id, action, qty, remarks, created_at)
            VALUES (?, 'Allocated', ?, 'Stock allocated to event', ?)
        """, (item_id, qty, now()))
        self.redirect("/allocate")

    def return_item(self, form):
        allocation_id = int(form["allocation_id"])
        allocation = query_all("SELECT * FROM allocations WHERE id=?", (allocation_id,))[0]
        if allocation["status"] == "Returned":
            self.redirect("/allocate")
            return
        execute("UPDATE allocations SET status='Returned', returned_at=? WHERE id=?", (now(), allocation_id))
        execute("UPDATE items SET available_qty = available_qty + ? WHERE id=?", (allocation["qty"], allocation["item_id"]))
        execute("""
            INSERT INTO transactions(item_id, action, qty, remarks, created_at)
            VALUES (?, 'Returned', ?, 'Stock returned from event', ?)
        """, (allocation["item_id"], allocation["qty"], now()))
        self.redirect("/allocate")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    init_db()
    server = HTTPServer((HOST, PORT), SmartInventoryHandler)
    print(f"Smart Inventory Management running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    server.serve_forever()


if __name__ == "__main__":
    main()
