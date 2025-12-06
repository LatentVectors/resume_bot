/**
 * Hook for initializing job intake session with analyses.
 * 
 * Handles creating the intake session and running gap/stakeholder analyses
 * before transitioning to Step 2 (Experience).
 */

import { useState, useCallback } from "react";
import { jobsAPI } from "@/lib/api/jobs";
import { experiencesAPI } from "@/lib/api/experiences";
import { langgraphWorkflowsAPI } from "@/lib/api/workflows";
import { formatAllExperiences } from "@/lib/utils/formatExperiences";
import type { Achievement } from "@resume/database/types";

interface IntakeInitializationResult {
  sessionId: number;
  gapAnalysis: string;
  stakeholderAnalysis: string;
}

interface UseIntakeInitializationReturn {
  /**
   * Initialize intake session with analyses for a job.
   * Creates session if needed, runs analyses if missing, saves to session.
   */
  initializeIntake: (params: {
    jobId: number;
    userId: number;
    jobDescription: string;
    forceRegenerate?: boolean;
  }) => Promise<IntakeInitializationResult>;
  
  /** Whether initialization is in progress */
  isInitializing: boolean;
  
  /** Current status message for UI display */
  statusMessage: string | null;
  
  /** Error message if initialization failed */
  error: string | null;
}

export function useIntakeInitialization(): UseIntakeInitializationReturn {
  const [isInitializing, setIsInitializing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const initializeIntake = useCallback(
    async (params: {
      jobId: number;
      userId: number;
      jobDescription: string;
      forceRegenerate?: boolean;
    }): Promise<IntakeInitializationResult> => {
      const { jobId, userId, jobDescription, forceRegenerate = false } = params;
      
      setIsInitializing(true);
      setStatusMessage("Creating intake session...");
      setError(null);

      try {
        // Step 1: Get or create intake session
        let session;
        try {
          session = await jobsAPI.getIntakeSession(jobId);
        } catch {
          // Session doesn't exist, create it
          session = await jobsAPI.createIntakeSession(jobId);
        }

        // Check if analyses already exist and we don't need to regenerate
        const needsGapAnalysis = forceRegenerate || !session.gap_analysis?.trim();
        const needsStakeholderAnalysis = forceRegenerate || !session.stakeholder_analysis?.trim();

        // If both analyses exist and we're not forcing regeneration, return early
        if (!needsGapAnalysis && !needsStakeholderAnalysis) {
          setStatusMessage(null);
          setIsInitializing(false);
          return {
            sessionId: session.id,
            gapAnalysis: session.gap_analysis || "",
            stakeholderAnalysis: session.stakeholder_analysis || "",
          };
        }

        // Step 2: Fetch and format user experiences
        setStatusMessage("Loading your experience data...");
        const experiences = await experiencesAPI.list(userId);
        
        // Fetch achievements for each experience
        const achievementsByExp = new Map<number, Achievement[]>();
        await Promise.all(
          experiences.map(async (exp) => {
            try {
              const achievements = await experiencesAPI.listAchievements(exp.id);
              achievementsByExp.set(exp.id, achievements);
            } catch (err) {
              console.error(`Failed to fetch achievements for experience ${exp.id}:`, err);
            }
          })
        );

        const workExperience = formatAllExperiences(experiences, achievementsByExp);

        let gapAnalysis = session.gap_analysis || "";
        let stakeholderAnalysis = session.stakeholder_analysis || "";

        // Step 3: Run gap analysis if needed
        if (needsGapAnalysis) {
          setStatusMessage("Analyzing job requirements...");
          try {
            const gapResponse = await langgraphWorkflowsAPI.gapAnalysis({
              job_description: jobDescription,
              work_experience: workExperience,
            });
            gapAnalysis = gapResponse.analysis;

            if (!gapAnalysis?.trim()) {
              throw new Error("Gap analysis returned empty result");
            }

            // Save gap analysis immediately
            await jobsAPI.updateIntakeSession(jobId, {
              gap_analysis: gapAnalysis,
            });
          } catch (err) {
            console.error("Gap analysis failed:", err);
            throw new Error("Failed to analyze job requirements. Please try again.");
          }
        }

        // Step 4: Run stakeholder analysis if needed
        if (needsStakeholderAnalysis) {
          setStatusMessage("Analyzing hiring stakeholders...");
          try {
            const stakeholderResponse = await langgraphWorkflowsAPI.stakeholderAnalysis({
              job_description: jobDescription,
              work_experience: workExperience,
            });
            stakeholderAnalysis = stakeholderResponse.analysis;

            if (!stakeholderAnalysis?.trim()) {
              throw new Error("Stakeholder analysis returned empty result");
            }

            // Save stakeholder analysis
            await jobsAPI.updateIntakeSession(jobId, {
              stakeholder_analysis: stakeholderAnalysis,
            });
          } catch (err) {
            console.error("Stakeholder analysis failed:", err);
            throw new Error("Failed to analyze hiring stakeholders. Please try again.");
          }
        }

        // Step 5: Mark step 1 as complete and update to step 2
        setStatusMessage("Finalizing...");
        await jobsAPI.updateIntakeSession(jobId, {
          current_step: 2,
          step_completed: 1,
        });

        setStatusMessage(null);
        setIsInitializing(false);

        return {
          sessionId: session.id,
          gapAnalysis,
          stakeholderAnalysis,
        };
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "An unexpected error occurred";
        setError(errorMessage);
        setStatusMessage(null);
        setIsInitializing(false);
        throw err;
      }
    },
    []
  );

  return {
    initializeIntake,
    isInitializing,
    statusMessage,
    error,
  };
}

