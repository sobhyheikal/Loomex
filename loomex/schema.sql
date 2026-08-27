-- Loomex database schema
-- Run this in Supabase: Project → SQL Editor → New Query → paste all → Run

create extension if not exists pgcrypto;

-- Products
create table products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  description text,
  category text not null check (category in ('tops', 'tank-tops', 'pants', 'shorts')),
  price numeric(10,2) not null,
  sizes text[] not null default '{"S","M","L","XL"}',
  colors text[] not null default '{}',
  image_url text,
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
('Relaxed Jogger Pants', 'relaxed-jogger-pants', 'Loomex''s signature jogger, tapered leg, deep pockets.', 'pants', 750.00, '{"S","M","L","XL"}', '{"Black","Olive"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex'),
('Loop-Back Shorts', 'loop-back-shorts', 'Loop-back cotton shorts for lounging or the gym.', 'shorts', 420.00, '{"S","M","L","XL"}', '{"Black","Sand","Olive"}', 'https://placehold.co/600x750/201c18/f1ece2?text=Loomex');
