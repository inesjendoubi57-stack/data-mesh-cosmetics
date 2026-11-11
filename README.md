# data-mesh-cosmetics

## Merchandising database

The merchandising service stores products in SQLite at
`backend/merchandising/products.db`. The database and `products` table are
created automatically when the service starts. The two example products are
inserted only when the table is empty, so changes remain available after a
restart.

The fulfillment and customer finance services use separate SQLite databases at
`backend/fulfillment/fulfillment.db` and
`backend/customer_finance/customer_finance.db`. Their tables and example records
are created automatically on startup, and changes persist across restarts.