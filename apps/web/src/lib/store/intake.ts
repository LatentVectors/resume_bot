import { create } from "zustand";

/**
 * Job intake workflow step types.
 */
export type IntakeStep = "details" | "experience" | "proposals";

/**
 * Job details form data for intake workflow step 1.
 */
export interface JobDetailsFormData {
  title: string;
  company: string;
  description: string;
}

/**
 * Experience selection data for intake workflow step 2.
 */
export interface ExperienceSelectionData {
  selectedExperienceIds: number[];
  gapAnalysisResults?: unknown; // Will be typed when gap analysis API is integrated
}

/**
 * Job intake workflow store for managing multi-step intake process state.
 */
interface IntakeStore {
  /** Current job ID being processed */
  jobId: number | null;
  /** Current step in the intake workflow */
  currentStep: IntakeStep | null;
  /** Job details form data (step 1) */
  jobDetails: JobDetailsFormData | null;
  /** Experience selection data (step 2) */
  experienceSelection: ExperienceSelectionData | null;
  /** Session ID for tracking intake workflow */
  sessionId: string | null;

  /** Set the current job ID */
  setJobId: (jobId: number | null) => void;
  /** Set the current step */
  setCurrentStep: (step: IntakeStep | null) => void;
  /** Set job details form data */
  setJobDetails: (details: JobDetailsFormData | null) => void;
  /** Set experience selection data */
  setExperienceSelection: (selection: ExperienceSelectionData | null) => void;
  /** Set session ID */
  setSessionId: (sessionId: string | null) => void;
  /** Clear all intake state */
  clearIntake: () => void;
}

export const useIntakeStore = create<IntakeStore>((set) => ({
  jobId: null,
  currentStep: null,
  jobDetails: null,
  experienceSelection: null,
  sessionId: null,

  setJobId: (jobId) => set({ jobId }),
  setCurrentStep: (step) => set({ currentStep: step }),
  setJobDetails: (details) => set({ jobDetails: details }),
  setExperienceSelection: (selection) => set({ experienceSelection: selection }),
  setSessionId: (sessionId) => set({ sessionId }),
  clearIntake: () =>
    set({
      jobId: null,
      currentStep: null,
      jobDetails: null,
      experienceSelection: null,
      sessionId: null,
    }),
}));

