import fs from 'node:fs';
import path from 'node:path';
import { requireSupabaseAdminEnv } from './env.js';

const { url, serviceKey } = requireSupabaseAdminEnv();

const response = await fetch(`${url}/rest/v1/`, {
  headers: {
    apikey: serviceKey,
    Authorization: `Bearer ${serviceKey}`
  }
});

if (!response.ok) {
  throw new Error(`Supabase OpenAPI export failed: ${response.status} ${await response.text()}`);
}

const schema = await response.json();
const outputDir = path.resolve(process.cwd(), 'supabase');
fs.mkdirSync(outputDir, { recursive: true });

const filePath = path.join(outputDir, 'openapi.json');
fs.writeFileSync(filePath, `${JSON.stringify(schema, null, 2)}\n`);

console.log(`Wrote Supabase OpenAPI schema to ${filePath}`);
