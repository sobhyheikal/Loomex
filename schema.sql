-- Loomex database schema
-- Run this in Supabase: Project → SQL Editor → New Query → paste all → Run

create extension if not exists pgcrypto;

-- Products
create table products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  description text,
  category text not null check (category in ('tops', 'tank-tops', 'pants', 'pullovers', 'quarter-zips', 'jackets')),
  subcategory text check (subcategory is null or subcategory in ('joggers', 'checkered-pants')),
  price numeric(10,2) not null,
  sizes text[] not null default '{"S","M","L","XL"}',
  colors text[] not null default '{}',
  image_url text,
  color_images jsonb not null default '{}'::jsonb,  -- e.g. {"Black": "https://...", "Olive": "https://..."}
  in_stock boolean not null default true,
  created_at timestamptz not null default now()
);

-- Orders
create table orders (
  id uuid primary key default gen_random_uuid(),
  order_number text unique not null,
  customer_name text not null,
  phone text not null,
  address text not null,
  city text not null,
  payment_method text not null check (payment_method in ('cod', 'online')),
  payment_status text not null default 'pending',
  shipping numeric(10,2) not null default 0,
  total numeric(10,2) not null,
  status text not null default 'new',
  created_at timestamptz not null default now()
);

-- Order line items
create table order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders(id) on delete cascade,
  product_id uuid references products(id),
  product_name text not null,
  size text,
  color text,
  quantity int not null default 1,
  unit_price numeric(10,2) not null
);

-- Row Level Security
-- The website talks to Supabase using the SERVICE ROLE key, kept only on the
-- server (Vercel environment variables), never sent to the browser. The
-- service role key bypasses RLS by design, so the app works even with no
-- public policies below. We still enable RLS and add a narrow read-only
-- policy for products, in case you ever want to query products straight
-- from the browser later (e.g. a future "add to cart" JS widget).

alter table products enable row level security;
alter table orders enable row level security;
alter table order_items enable row level security;

create policy "Public can view in-stock products"
  on products for select
  using (in_stock = true);

-- No public policies on orders / order_items: only the server (service role)
-- can read or write orders. This keeps customer data private.

-- Sample products so you have something to look at immediately.
-- Replace image_url with real product photo URLs once you upload them to
-- Supabase Storage (see README, step 3.4).
insert into products (name, slug, description, category, price, sizes, colors, image_url) values
('Essential Crew Tee', 'essential-crew-tee', 'Heavyweight cotton tee cut for everyday wear.', 'tops', 450.00, '{"S","M","L","XL"}', '{"Black","Sand","White"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex'),
('Ribbed Tank', 'ribbed-tank', 'Fitted ribbed tank in soft stretch cotton.', 'tank-tops', 320.00, '{"S","M","L"}', '{"Black","Sand"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex'),
('Fleece Pullover', 'fleece-pullover', 'Brushed fleece pullover with a relaxed hood, built for layering on cool nights.', 'pullovers', 650.00, '{"S","M","L","XL"}', '{"Black","Sand","Olive"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex'),
('Brushed Quarter-Zip', 'brushed-quarter-zip', 'Half-zip pullover in brushed fleece, a clean layer for cooler mornings.', 'quarter-zips', 680.00, '{"S","M","L","XL"}', '{"Black","Olive"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex'),
('Loomex Field Jacket', 'loomex-field-jacket', 'Heavyweight field jacket built to layer over everything else.', 'jackets', 1200.00, '{"S","M","L","XL"}', '{"Black","Olive"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex');

-- Pants: joggers and checkered-pants subcategories. Jogger pants get a photo
-- per color, used to power the color carousel on their product page.
insert into products (name, slug, description, category, subcategory, price, sizes, colors, image_url, color_images) values
('Relaxed Jogger Pants', 'relaxed-jogger-pants', 'Loomex''s signature jogger, tapered leg, deep pockets.', 'pants', 'joggers', 750.00, '{"S","M","L","XL"}', '{"Black","Olive"}',
 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex+Black',
 '{"Black": "https://placehold.co/600x750/201c18/f1ece2?text=Loomex+Black", "Olive": "https://placehold.co/600x750/4f6d3a/f1ece2?text=Loomex+Olive"}');

insert into products (name, slug, description, category, subcategory, price, sizes, colors, image_url) values
('Cuffed Jogger Pants', 'cuffed-jogger-pants', 'Tapered joggers in heavyweight cotton, cuffed at the ankle for an easy fit.', 'pants', 'joggers', 480.00, '{"S","M","L","XL"}', '{"Black","Sand","Olive"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex'),
('Checkered Flannel Pants', 'checkered-flannel-pants', 'Brushed flannel pants in a classic check, relaxed through the leg.', 'pants', 'checkered-pants', 520.00, '{"S","M","L","XL"}', '{"Black Check","Grey Check"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex');
