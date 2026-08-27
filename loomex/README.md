# Loomex — setup guide

A mobile-first storefront for Loomex: FastAPI (Python) + Supabase (database)
+ Vercel (hosting), with Cash on Delivery and an online-payment slot ready
to wire up. Follow the steps in order — each one only takes a few minutes.

---

## 0. What you'll have accounts on

- [GitHub](https://github.com) — free
- [Supabase](https://supabase.com) — free tier is enough to start
- [Vercel](https://vercel.com) — free "Hobby" tier is enough to start

---

## 1. Create the GitHub repository

1. Go to github.com → click **New repository**.
2. Name it `loomex` (or whatever you like), set it to **Private** (recommended
   while you're building), don't add a README/gitignore (we already have them).
3. On your computer, open a terminal in this project folder and run:

```bash
git init
git add .
git commit -m "Initial Loomex storefront"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/loomex.git
git push -u origin main
```

Your code is now on GitHub. Every push to `main` will later auto-deploy to
Vercel once step 5 is done.

---

## 2. Create the Supabase project

1. Go to supabase.com → **New project**.
2. Pick a name (`loomex`), a strong database password (save it somewhere safe),
   and a region close to your customers (e.g. an EU or Middle East region).
3. Wait ~2 minutes for it to provision.

### 2.1 Create the tables

1. In the Supabase dashboard, open **SQL Editor** → **New query**.
2. Open `schema.sql` from this project, copy everything, paste it in, click **Run**.
3. This creates `products`, `orders`, and `order_items`, turns on Row Level
   Security, and inserts 4 sample products so the site isn't empty on first run.

### 2.2 Get your API keys

Go to **Settings → API**. You need two values for the next step:
- **Project URL**
- **service_role secret key** (click "Reveal" — not the `anon` key)

Keep the service_role key private; it has full database access.

---

## 3. Run the site locally

1. Install Python 3.12 if you don't have it.
2. In the project folder:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

3. Open `.env` and paste in your Supabase URL and service_role key from step 2.2.
4. Run it:

```bash
uvicorn main:app --reload
```

5. Open `http://127.0.0.1:8000` — you should see the Loomex homepage with the
   4 sample products. Click through to a product, place a test order, and
   check **Supabase → Table Editor → orders** to confirm it saved.

### 3.3 Add your real products

Easiest way for now: **Supabase → Table Editor → products → Insert row**.
Fill in name, slug (URL-friendly, e.g. `essential-crew-tee`), category
(must be exactly `tops`, `tank-tops`, `pants`, or `shorts`), price, sizes,
colors, and an image URL. You can delete the 4 sample rows once you have
your own.

### 3.4 Product photos

Supabase → **Storage** → create a bucket called `products` → set it to
**Public** → upload your photos there. Click a file → **Copy URL** → paste
that into the product's `image_url` field.

---

## 4. Push your changes

Any time you make changes locally:

```bash
git add .
git commit -m "describe what changed"
git push
```

---

## 5. Deploy to Vercel

1. Go to vercel.com → **Add New → Project**.
2. **Import** your `loomex` GitHub repo (you'll be asked to connect your
   GitHub account the first time).
3. Vercel auto-detects this as a Python/FastAPI project — you don't need to
   change the build settings.
4. Before clicking Deploy, expand **Environment Variables** and add:
   - `SUPABASE_URL` → your project URL
   - `SUPABASE_SERVICE_KEY` → your service_role key
5. Click **Deploy**. In about a minute you'll get a live URL like
   `loomex.vercel.app`.

From now on, every `git push` to `main` automatically redeploys the live site.

### 5.1 Custom domain

Vercel → your project → **Settings → Domains** → add `loomex.com` (or
whatever you buy) and follow the DNS instructions it gives you.

---

## 6. Online payment (when you're ready)

Cash on Delivery works out of the box. For online payments, Egypt-friendly
options that support cards and mobile wallets:

- **[Paymob](https://paymob.com)** — widely used by Egyptian small brands, has a hosted checkout iframe.
- **[Kashier](https://kashier.io)** — similar, good docs.
- **[Fawry](https://fawry.com)** — strong if you want Fawry-pay-at-kiosk as an option too.

Once you sign up and get API keys, open `main.py` and look for the comment
block **"ONLINE PAYMENT INTEGRATION POINT"** inside the `place_order`
function — that's exactly where to call the gateway's API and redirect the
customer to their hosted payment page instead of straight to the success page.
Each gateway's docs include a Python/HTTP example you can drop in there.

---

## What's deliberately left simple (next steps once you're validating demand)

- **One item per checkout**, not a multi-item cart — keeps the MVP small.
  A real cart (stored in the browser, or a `cart` table) is a natural v2.
- **No admin panel** — you manage products and view orders directly in the
  Supabase Table Editor, which is genuinely fine at low volume.
- **No email/SMS confirmation** — worth adding once you're ready (Supabase
  has built-in email sending, or use a service like Twilio for SMS).
