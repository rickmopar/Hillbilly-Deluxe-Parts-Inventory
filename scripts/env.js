import fs from 'node:fs';
import path from 'node:path';

export function loadEnv(fileName = '.env.local') {
  const envPath = path.resolve(process.cwd(), fileName);
  if (!fs.existsSync(envPath)) return {};

  const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
  const values = {};

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const equalsAt = trimmed.indexOf('=');
    if (equalsAt === -1) continue;

    const key = trimmed.slice(0, equalsAt).trim();
    let value = trimmed.slice(equalsAt + 1).trim();

    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }

    values[key] = value;
  }

  return values;
}

export function requireSupabaseAdminEnv() {
  const localEnv = loadEnv();
  const env = { ...localEnv, ...process.env };
  const url = env.SUPABASE_URL;
  const serviceKey = env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceKey) {
    throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. Add them to .env.local.');
  }

  return { url: url.replace(/\/$/, ''), serviceKey };
}
