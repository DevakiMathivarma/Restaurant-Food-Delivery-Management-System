# ER Diagram — Restaurant & Food Delivery Management System

This diagram shows all 16 tables and how they connect. GitHub renders this
automatically when viewing this file in a repository — no separate image or
tool needed. Full field lists for every table are in `app/models/` and the
Alembic migration file.

```mermaid
erDiagram
    USER ||--o| CUSTOMER : "has profile"
    USER ||--o| DELIVERY_PARTNER : "has profile"
    USER ||--o{ RESTAURANT : "owns (as owner_id)"
    USER ||--o{ AUDIT_LOG : "performs (optional)"

    CUSTOMER ||--o{ ADDRESS : "saves"
    CUSTOMER ||--o| CART : "has"
    CUSTOMER ||--o{ ORDER : "places"
    CUSTOMER ||--o{ REVIEW : "writes"

    RESTAURANT ||--o{ MENU_ITEM : "lists"
    RESTAURANT ||--o{ ORDER : "receives"

    CART ||--o{ CART_ITEM : "contains"
    MENU_ITEM ||--o{ CART_ITEM : "added as"
    MENU_ITEM ||--o{ ORDER_ITEM : "ordered as"

    ORDER ||--o{ ORDER_ITEM : "contains"
    ORDER ||--o{ ORDER_TRACKING : "logs"
    ORDER ||--o{ PAYMENT : "collects"
    ORDER ||--o| REFUND : "may have"
    ORDER ||--o| REVIEW : "may have"
    ORDER }o--o| COUPON : "may use"
    ORDER }o--o| DELIVERY_PARTNER : "may be assigned"
    ORDER }o--|| ADDRESS : "delivers to"

    DELIVERY_PARTNER ||--o{ ORDER : "delivers"

    USER {
        int id PK
        string full_name
        string email UK
        string phone UK
        string password_hash
        enum role
        bool is_active
    }

    RESTAURANT {
        int id PK
        string restaurant_name
        int owner_id FK
        string city
        string cuisine_type
        time opening_time
        time closing_time
        enum status
        decimal delivery_radius
    }

    MENU_ITEM {
        int id PK
        int restaurant_id FK
        string category
        string name
        decimal price
        bool availability
        bool vegetarian
        int spicy_level
    }

    CUSTOMER {
        int id PK
        int user_id FK
    }

    ADDRESS {
        int id PK
        int customer_id FK
        string address_line
        string city
        string pincode
        decimal latitude
        decimal longitude
        enum address_type
        bool is_default
    }

    CART {
        int id PK
        int customer_id FK "unique"
        int restaurant_id FK "nullable lock"
    }

    CART_ITEM {
        int id PK
        int cart_id FK
        int menu_item_id FK
        int quantity
    }

    COUPON {
        int id PK
        string coupon_code UK
        enum discount_type
        decimal discount_value
        decimal minimum_order_value
        int usage_limit
        int times_used
        enum status
    }

    ORDER {
        int id PK
        string order_number UK
        int customer_id FK
        int restaurant_id FK
        int address_id FK
        int coupon_id FK
        int delivery_partner_id FK
        decimal subtotal
        decimal total_amount
        enum order_status
        enum payment_status
    }

    ORDER_ITEM {
        int id PK
        int order_id FK
        int menu_item_id FK
        string item_name
        decimal price_at_order
        int quantity
    }

    DELIVERY_PARTNER {
        int id PK
        int user_id FK
        enum vehicle_type
        string vehicle_number UK
        enum availability_status
        decimal current_latitude
        decimal current_longitude
    }

    ORDER_TRACKING {
        int id PK
        int order_id FK
        string status
        string notes
        int updated_by_user_id FK
    }

    PAYMENT {
        int id PK
        int order_id FK
        decimal amount
        enum payment_method
        string transaction_id UK
        enum status
    }

    REFUND {
        int id PK
        int order_id FK "unique"
        decimal refund_amount
        enum status
        int processed_by_user_id FK
    }

    REVIEW {
        int id PK
        int order_id FK "unique"
        int customer_id FK
        int restaurant_rating
        int delivery_rating
    }

    AUDIT_LOG {
        int id PK
        int user_id FK
        string action
        string entity_type
        int entity_id
    }
```

---

## Relationships explained in plain words

- **One User can have one Customer profile, and separately, one Delivery
  Partner profile** — a single account only ever holds one of these, matching
  its role, but the schema itself allows both relationships from `User`.
- **One User (a Restaurant Owner) can own many Restaurants.**
- **One Customer can save many Addresses, has exactly one Cart, places many
  Orders, and writes many Reviews.**
- **One Restaurant lists many Menu Items, and receives many Orders.**
- **One Cart contains many Cart Items** — but the Cart itself locks to a
  single Restaurant the moment its first item is added, released again once
  it's emptied.
- **One Order branches into several things:** many Order Items (a permanent,
  locked-in snapshot of name and price — never recalculated later), many
  Order Tracking entries (its full status history), many Payments, and at
  most **one** Refund and at most **one** Review — both enforced by a real
  `unique` constraint on `order_id`, not just application logic.
- **An Order optionally uses one Coupon**, and optionally has one Delivery
  Partner assigned — both genuinely optional, since not every order needs a
  discount, and assignment happens as a separate step after the order is
  placed.
- **One Delivery Partner delivers many Orders** over time, though only ever
  one *active* one at a time (enforced through their `availability_status`,
  not a database constraint).
- **Audit Log entries optionally point back to whichever User performed the
  action** — optional so the log entry survives even if that user's account
  is later removed.

## How to view this diagram

- **On GitHub:** just open this file in your repository — it renders
  automatically, no setup needed.
- **Locally, before pushing:** paste the code block above (without the triple
  backticks) into [mermaid.live](https://mermaid.live) to preview it instantly.