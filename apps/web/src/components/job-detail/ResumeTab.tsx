"use client";

import { ExperienceResumeInterface } from "@/components/intake/ExperienceResumeInterface";
import type { components } from "@/types/api";

type JobStatus = components["schemas"]["JobStatus"];

interface ResumeTabProps {
  jobId: number;
  jobDescription?: string;
  jobStatus: JobStatus;
}

export function ResumeTab({ jobId }: ResumeTabProps) {
  return (
    <ExperienceResumeInterface
      jobId={jobId}
      showStepTitle={false}
      showFooter={false}
    />
  );
}
