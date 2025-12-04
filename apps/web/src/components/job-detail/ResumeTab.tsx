"use client";

import { ExperienceResumeInterface } from "@/components/intake/ExperienceResumeInterface";
import type { JobStatus } from "@resume/database/types";

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
