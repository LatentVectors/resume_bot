/**
 * Seed Templates Script
 *
 * Migrates HTML template files from apps/api/src/features/*/templates/
 * into the Supabase templates table.
 *
 * Usage:
 *   npx tsx scripts/seed-templates.ts
 *
 * This script is idempotent - it will skip templates that already exist by name.
 */

import { createClient } from "@supabase/supabase-js";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321";
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

// Template source directories (relative to monorepo root)
const MONOREPO_ROOT = path.resolve(__dirname, "../../..");
const TEMPLATE_SOURCES = [
  {
    dir: path.join(MONOREPO_ROOT, "apps/api/src/features/resume/templates"),
    type: "resume" as const,
  },
  {
    dir: path.join(MONOREPO_ROOT, "apps/api/src/features/cover_letter/templates"),
    type: "cover_letter" as const,
  },
];

interface TemplateData {
  name: string;
  type: "resume" | "cover_letter";
  html_content: string;
  description: string | null;
  preview_image_url: string | null;
  is_default: boolean;
  metadata: Record<string, unknown>;
}

/**
 * Read all HTML template files from a directory
 */
function readTemplateFiles(
  sourceDir: string,
  type: "resume" | "cover_letter"
): TemplateData[] {
  const templates: TemplateData[] = [];

  if (!fs.existsSync(sourceDir)) {
    console.warn(`  ⚠️ Directory not found: ${sourceDir}`);
    return templates;
  }

  const files = fs.readdirSync(sourceDir).filter((f) => f.endsWith(".html"));

  for (const file of files) {
    const filePath = path.join(sourceDir, file);
    const htmlContent = fs.readFileSync(filePath, "utf-8");

    // Use filename as template name for backward compatibility
    // e.g., "resume_000.html", "cover_000.html"
    const templateName = file;

    // Determine if this is the default template (index 000)
    const isDefault = file.includes("_000.html");

    // Extract a description based on the template
    let description: string | null = null;
    if (type === "resume") {
      const index = file.match(/_(\d+)\.html/)?.[1];
      description = index ? `Resume Template ${parseInt(index) + 1}` : null;
    } else if (type === "cover_letter") {
      const index = file.match(/_(\d+)\.html/)?.[1];
      description = index ? `Cover Letter Template ${parseInt(index) + 1}` : null;
    }

    templates.push({
      name: templateName,
      type,
      html_content: htmlContent,
      description,
      preview_image_url: null,
      is_default: isDefault,
      metadata: {
        source_file: file,
        migrated_at: new Date().toISOString(),
      },
    });
  }

  return templates;
}

/**
 * Main seed function
 */
async function seedTemplates() {
  console.log("🌱 Starting template seeding...\n");

  // Validate environment
  if (!SUPABASE_SERVICE_ROLE_KEY) {
    console.error("❌ SUPABASE_SERVICE_ROLE_KEY environment variable is required");
    console.log("   Set it in your environment or .env file");
    process.exit(1);
  }

  // Create Supabase admin client
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });

  // Collect all templates from source directories
  const allTemplates: TemplateData[] = [];
  for (const source of TEMPLATE_SOURCES) {
    console.log(`📁 Reading ${source.type} templates from: ${source.dir}`);
    const templates = readTemplateFiles(source.dir, source.type);
    allTemplates.push(...templates);
    console.log(`   Found ${templates.length} template(s)\n`);
  }

  if (allTemplates.length === 0) {
    console.log("⚠️ No templates found to seed");
    return;
  }

  console.log(`📊 Total templates to seed: ${allTemplates.length}\n`);

  // Get existing templates
  const { data: existingTemplates, error: fetchError } = await supabase
    .from("templates")
    .select("name");

  if (fetchError) {
    console.error("❌ Failed to fetch existing templates:", fetchError.message);
    process.exit(1);
  }

  const existingNames = new Set(existingTemplates?.map((t) => t.name) ?? []);

  // Insert templates
  let insertedCount = 0;
  let skippedCount = 0;

  for (const template of allTemplates) {
    if (existingNames.has(template.name)) {
      console.log(`⏭️  Skipping "${template.name}" (already exists)`);
      skippedCount++;
      continue;
    }

    const { error: insertError } = await supabase.from("templates").insert({
      name: template.name,
      type: template.type,
      html_content: template.html_content,
      description: template.description,
      preview_image_url: template.preview_image_url,
      is_default: template.is_default,
      metadata: template.metadata,
    });

    if (insertError) {
      console.error(`❌ Failed to insert "${template.name}":`, insertError.message);
      continue;
    }

    console.log(`✅ Inserted "${template.name}" (${template.type})`);
    insertedCount++;
  }

  console.log("\n📈 Seeding Summary:");
  console.log(`   Inserted: ${insertedCount}`);
  console.log(`   Skipped:  ${skippedCount}`);
  console.log(`   Total:    ${allTemplates.length}`);
  console.log("\n✨ Template seeding complete!");
}

// Run the script
seedTemplates().catch((error) => {
  console.error("❌ Unexpected error:", error);
  process.exit(1);
});

