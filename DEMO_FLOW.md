# Mandatory Demo Flow 

This explains exactly what happens, step by step, when someone uses the app to
order food — from a restaurant setting up their menu, through a customer
placing an order, all the way to delivery and a review — including the
background things (emails, live tracking, real coordinates) that happen
automatically without anyone clicking a separate button for them.

---

## 1. Register

Before anything else can happen, people need accounts. Here's how each type
of account actually gets created:

- The very first account, the **Admin**, is created automatically the moment
  the app starts — nobody has to sign it up.
- The Admin then creates a **Restaurant Owner** account for someone who runs
  a real restaurant.
- That Restaurant Owner can then create their own **Restaurant Staff**
  accounts — the people who actually work in their kitchen day to day.
- A **Customer** signs themselves up directly, with no login needed at all —
  exactly like downloading a food delivery app and creating your own account.
- A **Delivery Partner** also signs themselves up directly, the same way —
  matching how real delivery riders join these platforms on their own,
  entering their own vehicle details.


---

## 2. Create Restaurant

The Restaurant Owner lists their actual eatery on the platform — name,
address, cuisine type, opening and closing hours, and how far they're willing
to deliver.

**What's checked automatically:** the closing time genuinely has to be after
the opening time — you can't create a restaurant that claims to open at 10pm
and close at 9am. The restaurant starts out marked "Closed" — it only starts
accepting real orders once the owner explicitly opens it.

---

## 3. Add Menu

The Restaurant Owner (or their staff) adds real dishes to the menu — name,
category, price, whether it's vegetarian, how spicy it is.

**What's checked automatically:** the price has to genuinely be a positive
number — you can't list a dish for free or for a negative amount. Only the
restaurant's own owner or staff can touch that restaurant's menu — someone
else's restaurant account can't sneak in and edit it.

---

## 4. Customer Login

The customer logs in with the email and password they signed up with.

**What actually happens:** the app hands back two things — a short-lived
"access token" (used for every action afterward) and a longer-lived "refresh
token" (used only to get a fresh access token later, without typing the
password again).

---

## 5. Add Address

The customer saves a real delivery address — street, city, pincode.

**What happens automatically, behind the scenes:** the app takes that typed
address and sends it to a real, free mapping service (OpenStreetMap), asking
it to convert the address into genuine map coordinates — latitude and
longitude. If the address is recognized, those real coordinates get saved
alongside it. If a customer's very first address is added, it's automatically
marked as their default — there's no other sensible choice when it's the only
one they have. Adding a second address and marking it default automatically
un-defaults the first one, so a customer can never end up with two "default"
addresses at once.

---

## 6. Add Items to Cart

The customer picks dishes and adds them to their cart.

**What's checked automatically:** an item that's currently marked unavailable
can't be added at all. And here's the more interesting rule — a cart can only
ever hold items from one restaurant at a time. The moment the very first item
goes in, the cart quietly "locks" itself to that restaurant; trying to add a
dish from a different restaurant gets rejected, with a clear message telling
the customer to clear their cart first if they want to switch. Once the cart
is completely emptied again, that lock releases automatically, ready for a
different restaurant next time.

---

## 7. Apply Coupon

The customer optionally enters a discount code at checkout.

**What's checked automatically:** the coupon has to genuinely still be within
its valid date window — not yet started, or already expired, both get
rejected. The order also has to meet the coupon's minimum spend requirement.
The coupon can't have already been used up to its total usage limit. And
importantly, a customer can only ever successfully use any specific coupon
code once — trying to reuse a code they've already benefited from on an
earlier order gets rejected.

---

## 8. Place Order

This is the single biggest moment in the whole flow — the customer's cart
becomes a real, official order.

**A lot happens automatically, all at once:**
- The restaurant has to genuinely be open right now — a closed restaurant
  can't receive new orders
- Every item in the cart gets double-checked for availability one final time
- Each item's real name and price get permanently locked in — so if the
  restaurant changes a dish's price tomorrow, this specific order's own
  history stays accurate forever
- The total gets calculated automatically using one clear formula: subtotal,
  plus tax, plus a delivery fee, minus any coupon discount
- A **PDF invoice** gets generated on the spot — a real file showing every
  item, the restaurant's name, and the full price breakdown
- An order confirmation **email gets queued** to send, with that invoice
  attached — handled by a background system (Celery) so the customer doesn't
  have to sit and wait for the email to actually go out
- The customer's cart gets emptied automatically
- For anyone watching this order live through a real-time connection
  (similar to how a live delivery-tracking map updates on its own), the new
  order's status appears instantly

---

## 9. Payment

The customer pays for the order they just placed.

**What's checked automatically:** the amount charged always comes from the
order's own real total — never something the customer could type in
themselves. Each electronic payment (card, UPI, wallet) needs its own unique
transaction reference, and the same reference can never be reused for a
second payment. Cash-on-delivery is the one exception — it genuinely doesn't
need a transaction reference at all, since there's no digital transaction
happening. The moment payment succeeds, an email confirmation gets queued
automatically.

---

## 10. Assign Delivery Partner

Someone on the restaurant or admin side assigns a rider to actually deliver
the order.

**What's checked automatically:** only a delivery partner who's currently
marked "Available" can be assigned at all — someone already out on another
delivery, or currently offline, simply won't be offered. The instant they're
assigned, their own status automatically flips to "On Delivery," which also
means they can no longer manually change their own availability status until
this delivery is actually finished — preventing a rider from accidentally
declaring themselves free while still mid-delivery. An assignment email goes
out to the customer, and the live connection pushes an instant update too.

---

## 11. Track Order

As the order moves through the kitchen and out for delivery, its status
keeps updating — Accepted, Preparing, Ready, Picked Up, Out for Delivery.

**What happens automatically at every single one of these changes:** a
permanent history entry gets written down, recording exactly what changed and
when — building a real, complete timeline anyone can look back on later. Once
an order has genuinely finished (either delivered or cancelled), it can never
receive another status update after that point — the story is over. While the
delivery partner is actually out delivering, their live location updates get
pushed through the same real-time connection too, so watching this order
feels like watching a live map, not just a status label.

---

## 12. Deliver Order

The order finally reaches the customer, and gets marked "Delivered."

**What happens automatically, right at this moment:** the delivery partner
who completed it automatically becomes "Available" again, instantly ready for
their next delivery, without anyone needing to manually flip a switch. A
delivery confirmation email goes out to the customer. And this is the one
moment that unlocks the final step — only a genuinely delivered order can now
be reviewed.

---

## 13. Review

The customer shares their experience — how the food was, and separately, how
the delivery itself went.

**What's checked automatically:** only orders that have genuinely reached
"Delivered" can be reviewed at all — trying to review something still being
prepared, or an order that was cancelled, gets rejected. And the same order
can never be reviewed twice — one honest review per order, permanently.

---

## The Big Picture

```
Register (Admin → Restaurant Owner → Staff, Customer/Delivery Partner self-serve)
   → Create Restaurant (hours validated)
   → Add Menu (price validated, ownership scoped)
   → Customer Login (access + refresh tokens)
   → Add Address (real coordinates via free geocoding, only-one-default rule)
   → Add Items to Cart (one-restaurant lock, availability checked)
   → Apply Coupon (expiry, minimum spend, usage limit, one-per-customer)
   → Place Order (total calculated, PDF invoice, email, live update)
   → Payment (amount matched, duplicate transactions blocked)
   → Assign Delivery Partner (availability checked, conflict prevention)
   → Track Order (full history logged, live location updates)
   → Deliver Order (delivery partner freed up automatically, email sent)
   → Review (delivered-only, one review per order)
```

Every step that changes something important — an order's status, a coupon's
usage count, a delivery partner's availability — happens automatically, as a
direct result of the action taken. Nobody has to do the math by hand, remember
to send a notification, or manually check whether a rider is actually free.
The system keeps everything accurate and connected on its own, from the very
first restaurant listing all the way through to a delivered meal and an
honest review.