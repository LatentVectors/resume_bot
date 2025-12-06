/**
 * Prompts API client endpoints for fetching system prompts.
 *
 * NOTE: Prompts are currently out of scope for the API migration.
 * The prompts remain as file-based and need to be migrated in a future sprint.
 * For now, this API will throw errors indicating the feature is not available.
 */

export interface PromptResponse {
  name: string;
  prompt: string;
}

export const promptsAPI = {
  /**
   * Get a system prompt by name.
   *
   * NOTE: This feature is temporarily unavailable.
   * Prompts are stored as files and need to be migrated to the new API.
   *
   * @param promptName - Name of the prompt (gap_analysis, stakeholder_analysis, or resume_alignment_workflow)
   * @returns Promise resolving to the prompt response
   */
  async getPrompt(promptName: string): Promise<PromptResponse> {
    // TODO: Implement prompts API route to read from files or migrate to database
    throw new Error(
      `Prompts API is not yet migrated. Requested prompt: ${promptName}. ` +
        `This feature will be available in a future update.`
    );
  },
};
