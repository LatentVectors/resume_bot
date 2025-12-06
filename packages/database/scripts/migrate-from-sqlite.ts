/**
 * SQLite to Supabase Migration Script
 *
 * This script migrates data from the existing SQLite database to Supabase PostgreSQL.
 * Uses sql.js (pure JavaScript SQLite) for portability - no native bindings required.
 *
 * Only migrates data for user_id=1 (primary user).
 *
 * Usage:
 *   cd packages/database
 *   pnpm migrate:from-sqlite
 *
 * Environment Variables Required:
 *   NEXT_PUBLIC_SUPABASE_URL - Supabase API URL
 *   SUPABASE_SERVICE_ROLE_KEY - Service role key for admin access
 *   SQLITE_DATABASE_PATH - Path to SQLite database (default: ../data/resume_bot.db)
 */

import { createClient } from "@supabase/supabase-js";
import initSqlJs, { Database as SqlJsDatabase } from "sql.js";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

// ES module compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const SQLITE_DB_PATH =
  process.env.SQLITE_DATABASE_PATH ||
  path.resolve(__dirname, "../data/resume_bot.db");

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// Only migrate data for this user
const PRIMARY_USER_ID = 1;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error(
    "Error: Missing required environment variables NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
  );
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// SQLite table name to PostgreSQL table name mapping
// Note: resumes and cover_letters tables have been consolidated into their versions tables
// Note: messages, responses, and job_intake_chat_messages tables have been removed
const TABLE_NAME_MAP: Record<string, string> = {
  user: "users",
  experience: "experiences",
  achievement: "achievements",
  education: "education",
  certification: "certifications",
  job: "jobs",
  resumeversion: "resume_versions",
  coverletterversion: "cover_letter_versions",
  note: "notes",
  jobintakesession: "job_intake_sessions",
  experienceproposal: "experience_proposals",
};

// Columns to skip during migration (not needed in new schema)
const SKIP_COLUMNS: Record<string, string[]> = {
  jobintakesession: ["conversation_summary"],
  coverletterversion: ["cover_letter_id"], // FK removed in consolidated schema
};

// Enum value transformations
const ENUM_TRANSFORMS: Record<string, Record<string, string>> = {
  status: {
    NotSelected: "Not Selected",
    NoOffer: "No Offer",
  },
};

interface MigrationStats {
  table: string;
  sourceCount: number;
  migratedCount: number;
  skippedCount: number;
  errors: string[];
}

interface MigrationContext {
  jobIds: Set<number>;
  experienceIds: Set<number>;
  sessionIds: Set<number>;
  achievementIds: Set<number>;
  // Track latest resume/cover letter version per job for is_pinned
  latestResumeVersionByJob: Map<number, number>;
  latestCoverLetterVersionByJob: Map<number, number>;
}

/**
 * Pre-scan resume and cover letter versions to determine the latest version per job.
 * This is needed to set is_pinned correctly during migration.
 */
function preScanLatestVersions(
  db: SqlJsDatabase,
  ctx: MigrationContext,
  userId: number
): void {
  // Check and scan resume versions
  const resumeVersionCheck = db.exec(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='resumeversion'"
  );
  if (
    resumeVersionCheck.length > 0 &&
    resumeVersionCheck[0].values.length > 0
  ) {
    const resumeVersions = db.exec(
      `SELECT job_id, MAX(version_index) as max_version 
       FROM resumeversion 
       WHERE job_id IN (SELECT id FROM job WHERE user_id = ${userId})
       GROUP BY job_id`
    );
    if (resumeVersions.length > 0) {
      for (const row of resumeVersions[0].values) {
        const jobId = row[0] as number;
        const maxVersion = row[1] as number;
        ctx.latestResumeVersionByJob.set(jobId, maxVersion);
      }
    }
  }

  // Check and scan cover letter versions
  const coverLetterVersionCheck = db.exec(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='coverletterversion'"
  );
  if (
    coverLetterVersionCheck.length > 0 &&
    coverLetterVersionCheck[0].values.length > 0
  ) {
    const coverLetterVersions = db.exec(
      `SELECT job_id, MAX(version_index) as max_version 
       FROM coverletterversion 
       WHERE job_id IN (SELECT id FROM job WHERE user_id = ${userId})
       GROUP BY job_id`
    );
    if (coverLetterVersions.length > 0) {
      for (const row of coverLetterVersions[0].values) {
        const jobId = row[0] as number;
        const maxVersion = row[1] as number;
        ctx.latestCoverLetterVersionByJob.set(jobId, maxVersion);
      }
    }
  }
}

async function main() {
  console.log("=".repeat(60));
  console.log("SQLite to Supabase Migration");
  console.log("=".repeat(60));
  console.log(`SQLite Path: ${SQLITE_DB_PATH}`);
  console.log(`Supabase URL: ${SUPABASE_URL}`);
  console.log(`Primary User ID: ${PRIMARY_USER_ID}`);
  console.log("");

  // Check if SQLite file exists
  if (!fs.existsSync(SQLITE_DB_PATH)) {
    console.error(`Error: SQLite database not found at ${SQLITE_DB_PATH}`);
    process.exit(1);
  }

  // Initialize sql.js
  console.log("Initializing sql.js...");
  const SQL = await initSqlJs();

  // Read SQLite database
  console.log("Reading SQLite database...");
  const fileBuffer = fs.readFileSync(SQLITE_DB_PATH);
  const db = new SQL.Database(fileBuffer);

  const stats: MigrationStats[] = [];

  // Context to track IDs for filtering dependent tables
  const ctx: MigrationContext = {
    jobIds: new Set(),
    experienceIds: new Set(),
    sessionIds: new Set(),
    achievementIds: new Set(),
    latestResumeVersionByJob: new Map(),
    latestCoverLetterVersionByJob: new Map(),
  };

  // Pre-scan to find latest resume/cover letter version per job (needed for is_pinned)
  console.log("Pre-scanning for latest versions per job...");
  preScanLatestVersions(db, ctx, PRIMARY_USER_ID);
  console.log(
    `  Found latest resume versions for ${ctx.latestResumeVersionByJob.size} jobs`
  );
  console.log(
    `  Found latest cover letter versions for ${ctx.latestCoverLetterVersionByJob.size} jobs`
  );

  // Migration order with custom queries for filtering by user
  // Note: resume and coverletter tables removed - data consolidated into versions tables
  // Note: message, response, and jobintakechatmessage tables removed - data stored elsewhere
  const migrations: Array<{
    sqliteTable: string;
    query: string;
    collectIds?: (row: Record<string, unknown>, ctx: MigrationContext) => void;
  }> = [
    {
      sqliteTable: "user",
      query: `SELECT * FROM user WHERE id = ${PRIMARY_USER_ID}`,
    },
    {
      sqliteTable: "experience",
      query: `SELECT * FROM experience WHERE user_id = ${PRIMARY_USER_ID}`,
      collectIds: (row, ctx) => ctx.experienceIds.add(row.id as number),
    },
    {
      sqliteTable: "achievement",
      query: `SELECT * FROM achievement WHERE experience_id IN (SELECT id FROM experience WHERE user_id = ${PRIMARY_USER_ID})`,
      collectIds: (row, ctx) => ctx.achievementIds.add(row.id as number),
    },
    {
      sqliteTable: "education",
      query: `SELECT * FROM education WHERE user_id = ${PRIMARY_USER_ID}`,
    },
    {
      sqliteTable: "certification",
      query: `SELECT * FROM certification WHERE user_id = ${PRIMARY_USER_ID}`,
    },
    {
      sqliteTable: "job",
      query: `SELECT * FROM job WHERE user_id = ${PRIMARY_USER_ID}`,
      collectIds: (row, ctx) => ctx.jobIds.add(row.id as number),
    },
    {
      // Resume versions - is_pinned set based on pre-scanned latest versions
      sqliteTable: "resumeversion",
      query: `SELECT * FROM resumeversion WHERE job_id IN (SELECT id FROM job WHERE user_id = ${PRIMARY_USER_ID})`,
    },
    {
      // Cover letter versions - is_pinned set based on pre-scanned latest versions
      sqliteTable: "coverletterversion",
      query: `SELECT * FROM coverletterversion WHERE job_id IN (SELECT id FROM job WHERE user_id = ${PRIMARY_USER_ID})`,
    },
    {
      sqliteTable: "note",
      query: `SELECT * FROM note WHERE job_id IN (SELECT id FROM job WHERE user_id = ${PRIMARY_USER_ID})`,
    },
    {
      sqliteTable: "jobintakesession",
      query: `SELECT * FROM jobintakesession WHERE job_id IN (SELECT id FROM job WHERE user_id = ${PRIMARY_USER_ID})`,
      collectIds: (row, ctx) => ctx.sessionIds.add(row.id as number),
    },
    {
      sqliteTable: "experienceproposal",
      query: `SELECT * FROM experienceproposal WHERE session_id IN (SELECT id FROM jobintakesession WHERE job_id IN (SELECT id FROM job WHERE user_id = ${PRIMARY_USER_ID}))`,
    },
  ];

  // Migrate each table in order
  for (const migration of migrations) {
    const pgTable = TABLE_NAME_MAP[migration.sqliteTable];
    console.log(`\nMigrating ${migration.sqliteTable} → ${pgTable}...`);

    const tableStat = await migrateTable(
      db,
      migration.sqliteTable,
      pgTable,
      migration.query,
      ctx,
      migration.collectIds
    );
    stats.push(tableStat);
  }

  // Close SQLite database
  db.close();

  // Print summary
  printSummary(stats);

  // Reset sequences to prevent duplicate key errors
  await resetSequences();
}

async function migrateTable(
  db: SqlJsDatabase,
  sqliteTable: string,
  pgTable: string,
  query: string,
  ctx: MigrationContext,
  collectIds?: (row: Record<string, unknown>, ctx: MigrationContext) => void
): Promise<MigrationStats> {
  const stat: MigrationStats = {
    table: pgTable,
    sourceCount: 0,
    migratedCount: 0,
    skippedCount: 0,
    errors: [],
  };

  try {
    // Check if table exists in SQLite
    const tableCheck = db.exec(
      `SELECT name FROM sqlite_master WHERE type='table' AND name='${sqliteTable}'`
    );
    if (tableCheck.length === 0 || tableCheck[0].values.length === 0) {
      console.log(`  Table ${sqliteTable} does not exist in SQLite, skipping.`);
      return stat;
    }

    // Get filtered rows from SQLite table
    const result = db.exec(query);
    if (result.length === 0) {
      console.log(`  No data matching filter in ${sqliteTable}`);
      return stat;
    }

    const columns = result[0].columns;
    const rows = result[0].values;
    stat.sourceCount = rows.length;

    console.log(`  Found ${rows.length} rows`);

    // Transform rows
    const transformedRows: Record<string, unknown>[] = [];
    for (const row of rows) {
      const transformed = transformRow(sqliteTable, columns, row, ctx);

      // Collect IDs if needed for dependent tables
      if (collectIds) {
        collectIds(transformed, ctx);
      }

      transformedRows.push(transformed);
    }

    // Insert in batches to avoid timeouts
    const BATCH_SIZE = 100;
    for (let i = 0; i < transformedRows.length; i += BATCH_SIZE) {
      const batch = transformedRows.slice(i, i + BATCH_SIZE);

      const { data, error } = await supabase
        .from(pgTable)
        .insert(batch)
        .select();

      if (error) {
        stat.errors.push(
          `Batch ${Math.floor(i / BATCH_SIZE) + 1}: ${error.message}`
        );
        console.error(`  Error inserting batch: ${error.message}`);
      } else {
        stat.migratedCount += data?.length || 0;
      }
    }

    console.log(`  Migrated ${stat.migratedCount}/${stat.sourceCount} rows`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    stat.errors.push(message);
    console.error(`  Error: ${message}`);
  }

  return stat;
}

function transformRow(
  tableName: string,
  columns: string[],
  values: (string | number | null | Uint8Array)[],
  ctx: MigrationContext
): Record<string, unknown> {
  const row: Record<string, unknown> = {};

  // Get columns to skip for this table
  const skipColumns = SKIP_COLUMNS[tableName] || [];

  columns.forEach((col, index) => {
    // Skip columns that are not needed in the new schema
    if (skipColumns.includes(col)) {
      return;
    }

    let value = values[index];
    const columnName = col;

    // Transform values based on column type
    value = transformValue(tableName, columnName, value);

    row[columnName] = value;
  });

  // Add is_pinned and locked fields for version tables
  if (tableName === "resumeversion") {
    const jobId = row.job_id as number;
    const versionIndex = row.version_index as number;
    const latestVersion = ctx.latestResumeVersionByJob.get(jobId);
    row.is_pinned = versionIndex === latestVersion;
    row.locked = false;
  } else if (tableName === "coverletterversion") {
    const jobId = row.job_id as number;
    const versionIndex = row.version_index as number;
    const latestVersion = ctx.latestCoverLetterVersionByJob.get(jobId);
    row.is_pinned = versionIndex === latestVersion;
    row.locked = false;
    // Add event_type (new required field)
    row.event_type = "generate";
  }

  return row;
}

function transformValue(
  _tableName: string,
  columnName: string,
  value: string | number | null | Uint8Array
): unknown {
  if (value === null) return null;

  // Handle enum value transformations
  const enumTransform = ENUM_TRANSFORMS[columnName];
  if (enumTransform && typeof value === "string" && enumTransform[value]) {
    return enumTransform[value];
  }

  // Handle JSONB columns - parse JSON strings
  const jsonColumns = [
    "skills",
    "messages",
    "proposed_content",
    "original_proposed_content",
    "metadata",
  ];
  if (jsonColumns.includes(columnName) && typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      // If parsing fails, return as-is (might already be valid)
      return value;
    }
  }

  // Handle boolean columns (SQLite stores as 0/1)
  const booleanColumns = [
    "is_favorite",
    "has_resume",
    "has_cover_letter",
    "locked",
    "is_pinned",
    "ignore",
    "step1_completed",
    "step2_completed",
    "step3_completed",
    "is_default",
  ];
  if (booleanColumns.includes(columnName)) {
    return value === 1 || value === "1" || value === true;
  }

  // Handle datetime columns
  const dateTimeColumns = [
    "created_at",
    "updated_at",
    "applied_at",
    "sent_at",
    "completed_at",
  ];
  if (dateTimeColumns.includes(columnName) && typeof value === "string") {
    // SQLite datetime strings should be converted to ISO format
    try {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return date.toISOString();
      }
    } catch {
      // Keep original value if conversion fails
    }
  }

  // Handle date columns (DATE type, not TIMESTAMP)
  const dateColumns = ["start_date", "end_date", "grad_date", "date"];
  if (dateColumns.includes(columnName) && typeof value === "string") {
    // Extract just the date part (YYYY-MM-DD)
    const match = value.match(/^\d{4}-\d{2}-\d{2}/);
    if (match) {
      return match[0];
    }
  }

  return value;
}

/**
 * Reset PostgreSQL sequences for all tables that have auto-increment IDs.
 * This ensures that the next auto-generated ID is greater than any existing ID.
 */
async function resetSequences(): Promise<void> {
  console.log("\nResetting PostgreSQL sequences...");

  // Tables with auto-increment id columns
  // Note: resumes and cover_letters tables have been removed (consolidated into versions)
  // Note: messages, responses, and job_intake_chat_messages tables have been removed
  const tablesWithSequences = [
    "users",
    "experiences",
    "achievements",
    "education",
    "certifications",
    "jobs",
    "resume_versions",
    "cover_letter_versions",
    "notes",
    "job_intake_sessions",
    "experience_proposals",
  ];

  for (const table of tablesWithSequences) {
    try {
      // Get the max ID from the table
      const { data: maxData, error: maxError } = await supabase
        .from(table)
        .select("id")
        .order("id", { ascending: false })
        .limit(1)
        .single();

      if (maxError && maxError.code !== "PGRST116") {
        // PGRST116 = no rows returned, which is fine
        console.log(
          `  ⚠️ Could not get max ID for ${table}: ${maxError.message}`
        );
        continue;
      }

      const maxId = maxData?.id ?? 0;

      // Reset the sequence using raw SQL via RPC
      // Note: This requires a database function to be created, or we use a workaround
      // For now, we'll use the Supabase SQL editor approach via RPC if available
      console.log(`  ${table}: max id = ${maxId}`);

      // Call the reset_sequence function if it exists
      const { error: rpcError } = await supabase.rpc("reset_table_sequence", {
        table_name: table,
        new_value: maxId,
      });

      if (rpcError) {
        // Function might not exist yet - that's okay, we'll handle it
        if (
          rpcError.message.includes("function") ||
          rpcError.code === "42883"
        ) {
          console.log(
            `  ℹ️ reset_table_sequence function not found. Run the sequence reset SQL manually.`
          );
          break;
        } else {
          console.log(
            `  ⚠️ Error resetting sequence for ${table}: ${rpcError.message}`
          );
        }
      } else {
        console.log(`  ✅ Reset sequence for ${table} to ${maxId}`);
      }
    } catch (error) {
      console.log(
        `  ⚠️ Error processing ${table}: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  }

  console.log("\nSequence reset complete.");
  console.log(
    "If sequences were not reset automatically, run this SQL in your database:"
  );
  console.log(`
-- Reset all sequences to max(id) for each table
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_default LIKE 'nextval%'
    LOOP
        EXECUTE format(
            'SELECT setval(pg_get_serial_sequence(%L, %L), COALESCE((SELECT MAX(%I) FROM %I), 0) + 1, false)',
            t.table_name, t.column_name, t.column_name, t.table_name
        );
    END LOOP;
END $$;
  `);
}

function printSummary(stats: MigrationStats[]) {
  console.log("\n" + "=".repeat(60));
  console.log("Migration Summary");
  console.log("=".repeat(60));

  let totalSource = 0;
  let totalMigrated = 0;
  let totalErrors = 0;

  stats.forEach((stat) => {
    const status =
      stat.errors.length > 0
        ? "⚠️"
        : stat.migratedCount === stat.sourceCount
        ? "✅"
        : "⏳";
    console.log(
      `${status} ${stat.table}: ${stat.migratedCount}/${stat.sourceCount} rows`
    );
    if (stat.errors.length > 0) {
      stat.errors.forEach((err) => console.log(`   Error: ${err}`));
    }

    totalSource += stat.sourceCount;
    totalMigrated += stat.migratedCount;
    totalErrors += stat.errors.length;
  });

  console.log("-".repeat(60));
  console.log(`Total: ${totalMigrated}/${totalSource} rows migrated`);
  if (totalErrors > 0) {
    console.log(`Errors: ${totalErrors}`);
  }
  console.log("=".repeat(60));
}

main().catch((error) => {
  console.error("Migration failed:", error);
  process.exit(1);
});
