import os
import requests
from datetime import datetime
from flask import Flask, render_template, request

app = Flask(__name__)

FRANKFURTER_API = "https://api.frankfurter.dev/v1"
CURRENCIES = {}

def load_currencies():
    """Fetch all supported currency codes and full names."""
    global CURRENCIES
    if not CURRENCIES:
        try:
            res = requests.get(f"{FRANKFURTER_API}/currencies", timeout=10)
            if res.status_code == 200:
                CURRENCIES = res.json()
        except Exception:
            CURRENCIES = {
                "USD": "United States Dollar",
                "EUR": "Euro",
                "INR": "Indian Rupee",
                "GBP": "British Pound",
                "JPY": "Japanese Yen",
                "AUD": "Australian Dollar",
                "CAD": "Canadian Dollar"
            }
    return CURRENCIES

@app.route("/", methods=["GET", "POST"])
def index():
    currencies = load_currencies()
    result = None
    error = None

    # Get formatted current date
    today_date = datetime.now().strftime("%A, %d %B %Y")

    # Default values for form persistence
    from_curr = "USD"
    to_curr = "INR"
    amount = 1.0

    if request.method == "POST":
        from_curr = request.form.get("from_curr", "USD")
        to_curr = request.form.get("to_curr", "INR")
        raw_amount = request.form.get("amount", "1")

        try:
            amount = float(raw_amount)
            if amount <= 0:
                error = "Please enter an amount greater than 0."
        except ValueError:
            error = "Please enter a valid numeric amount."

        if not error:
            if from_curr == to_curr:
                unit_rate = 1.0
                total_converted = amount
                result = {
                    "from_curr": from_curr,
                    "to_curr": to_curr,
                    "from_name": currencies.get(from_curr, from_curr),
                    "to_name": currencies.get(to_curr, to_curr),
                    "amount": round(amount, 4),
                    "unit_rate": unit_rate,
                    "inverse_rate": 1.0,
                    "converted_amount": round(total_converted, 4),
                    "rate_date": today_date
                }
            else:
                try:
                    url = f"{FRANKFURTER_API}/latest"
                    params = {"base": from_curr, "symbols": to_curr}
                    res = requests.get(url, params=params, timeout=10)
                    data = res.json()

                    if "rates" in data and to_curr in data["rates"]:
                        unit_rate = data["rates"][to_curr]
                        total_converted = amount * unit_rate
                        inverse_rate = 1.0 / unit_rate if unit_rate != 0 else 0

                        result = {
                            "from_curr": from_curr,
                            "to_curr": to_curr,
                            "from_name": currencies.get(from_curr, from_curr),
                            "to_name": currencies.get(to_curr, to_curr),
                            "amount": round(amount, 4),
                            "unit_rate": round(unit_rate, 4),
                            "inverse_rate": round(inverse_rate, 4),
                            "converted_amount": round(total_converted, 4),
                            "rate_date": data.get("date", today_date)
                        }
                    else:
                        error = "Unable to obtain rate for selected currencies."
                except Exception:
                    error = "Exchange rate service unavailable. Please try again."

    return render_template(
        "index.html",
        currencies=currencies,
        from_curr=from_curr,
        to_curr=to_curr,
        amount=amount,
        result=result,
        error=error,
        today_date=today_date
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)