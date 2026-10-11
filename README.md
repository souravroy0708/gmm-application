# GMM Distributors - Ordering Platform (Phase 0-1 backend)

Django 5.2 LTS project with the full data model, business rules and a themed admin
(Django Unfold) for GMM Distributors Pvt. Ltd. Customer-facing pages (Phase 2) and
PDF invoices / proof-upload screens (Phase 3) build on top of this.

## Quick start (Linux)

```bash
python3 -m venv .venv && source .venv/bin/activate      # Python 3.10+ works; 3.12 recommended
pip install -r requirements.txt                          # or requirements.lock.txt for the exact tested versions
cp .env.example .env                                     # then edit SECRET_KEY
python manage.py migrate
python manage.py seed_demo                               # GMM details + 5 launch products (inactive, price 0)
python manage.py createsuperuser                         # asks for mobile number, name, password
python manage.py runserver
```

Open http://127.0.0.1:8000/admin/ and log in with your **mobile number** and password.
Run the tests with `python manage.py test` (41 tests).

## First things to do in the admin

1. **Business settings**: GSTIN, UPI ID / QR, bank details, COD limits, minimum order.
2. **Serviceable PIN codes**: add every PIN you deliver to, with delivery fee and COD allowed or not.
3. **Products > each product > packs**: set real pack sizes, SKU, price (GST-inclusive), GST rate,
   HSN code and stock, then tick *active*. Seeded packs are inactive with price 0 on purpose.
   Confirm GST rates and HSN codes with your CA - nothing here is tax advice.

## Layout

```
config/            settings (base / dev / prod), urls, wsgi, asgi
apps/core/         SiteSetting (business settings), Sequence (gap-free counters), PhoneField, seed_demo command
apps/accounts/     User (mobile number login, +91 normalised), Address (max 10, one default)
apps/catalog/      Category, Product, ProductVariant (pack, price, GST, stock), ProductImage, CropDose
apps/orders/       Order, OrderItem, OrderStatusLog, ServiceablePin + services.py (place_order, change_status)
apps/payments/     Payment (COD / UPI / bank proof) + services.py (submit_proof, set_status, mark_cod_collected)
apps/invoicing/    Invoice (GMM/2026-27/0001 style numbers, CGST+SGST or IGST) + services.py (issue_invoice)
```

## Rules enforced in code (see services.py)

- Prices include GST; tax is split out per line and stored on the order.
- Orders snapshot address, prices and tax, so later edits never change history.
- Stock is row-locked at checkout (no overselling); cancelling restores stock.
- `idempotency_key` makes a double tap or retry return the same order.
- Status flow: PLACED > CONFIRMED > PACKED > DISPATCHED > DELIVERED (cancel allowed until PACKED).
- UPI/bank orders cannot be dispatched until the payment proof is VERIFIED; the same UTR cannot back two payments.
- Invoice numbers are sequential per April-March financial year, never skipped, max 16 characters.
- Orders cannot be added or deleted by hand in the admin; staff use the actions (confirm, pack, dispatch,
  deliver, cancel, COD collected, issue invoice). Payments are verified or rejected (with a reason) in the Payments screen.

## Not built yet (next phases)

- Customer pages: catalogue, cart, checkout, order history (Phase 2).
- PDF invoice rendering, payment proof upload screen, email notifications, staff "order on behalf of customer" form (Phase 3).
- REST API and Flutter app (Phase 5).
- Production extras: PostgreSQL (`DATABASE_URL`), private object storage for payment proofs and invoices,
  2FA for staff (django-otp), a non-default `ADMIN_URL`, Sentry, backups.

## Production checklist

Use `DJANGO_SETTINGS_MODULE=config.settings.prod`, set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`,
`CSRF_TRUSTED_ORIGINS`, run `python manage.py collectstatic`, serve with gunicorn behind Nginx over HTTPS.
`python manage.py check --deploy` passes with the prod settings.
