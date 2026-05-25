# Hillbilly Deluxe Parts Inventory

Phone-first Mopar parts inventory backed by GitHub Pages and Supabase.

## Files

- `index.html` - main app
- `catalog-index.js` - starter Mopar catalog lookup index
- `supabase/schema.sql` - baseline schema and next-phase table plan
- `scripts/` - local Supabase admin helpers

## Local Supabase Admin Setup

Create `.env.local` locally. Do not commit it.

```env
SUPABASE_URL=https://dlhvjyxglgabkacnpmmq.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Then run:

```bash
npm run supabase:openapi
npm run backup:parts
```

The backup script writes JSON into `backups/`, which is ignored by Git.
