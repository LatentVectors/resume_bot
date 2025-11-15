"use client";

import { useParams } from "next/navigation";
import { ExperienceResumeInterface } from "@/components/intake/ExperienceResumeInterface";

export default function IntakeExperiencePage() {
  const params = useParams();
  const jobId = parseInt(params.jobId as string, 10);

  return (
    <ExperienceResumeInterface
              jobId={jobId}
      showStepTitle={true}
      showFooter={true}
    />
  );
}
