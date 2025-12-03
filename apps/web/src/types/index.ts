// Shared application types
// This file will contain TypeScript types that are shared across the application
// and are not generated from the API schema

import type { components } from "./api";

/**
 * Extended JobResponse that includes resume_chat_thread_id.
 * This extends the generated type until api.ts is regenerated.
 */
export interface JobResponseExtended
  extends components["schemas"]["JobResponse"] {
  resume_chat_thread_id?: string | null;
}

/**
 * Extended JobUpdate that includes resume_chat_thread_id.
 * This extends the generated type until api.ts is regenerated.
 */
export interface JobUpdateExtended extends components["schemas"]["JobUpdate"] {
  resume_chat_thread_id?: string | null;
}
