import fs from 'node:fs';
import path from 'node:path';
import { requireSupabaseAdminEnv } from './env.js';

const { url, serviceKey } = requireSupabaseAdminEnv();
const endpoint = `${url}/rest/v1/parts?select=*&order=created_at.desc`;

const response = await fetch(endpoint, {
  headers: {
    apikey: serviceKey,
    Authorization: `Bearer ${serviceKey}`
  }
});

if (!response.ok) {
  throw new Error(`Supabase parts backup failed: ${response.status} ${await response.text()}`);
}

const rows = await response.json();
const backupDir = path.resolve(process.cwd(), 'backups');
fs.mkdirSync(backupDir, { recursive: true });

const stamp = new Date().toISOString().replace(/[:.]/g, '-');
const filePath = path.join(backupDir, `parts-${stamp}.json`);
fs.writeFileSync(filePath, `${JSON.stringify(rows, null, 2)}\n`);

console.log(`Backed up ${rows.length} parts to ${filePath}`);
