"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, use } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OverviewTab } from "@/components/job-detail/OverviewTab";
import { ResumeTab } from "@/components/job-detail/ResumeTab";
import { CoverLetterTab } from "@/components/job-detail/CoverLetterTab";
import { NotesTab } from "@/components/job-detail/NotesTab";
import { useJob } from "@/lib/hooks/useJobs";

type TabValue = "overview" | "resume" | "cover" | "notes";

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resolvedParams = use(params);
  const jobId = parseInt(resolvedParams.id, 10);

  // Fetch job data
  const { data: job, isLoading, error } = useJob(jobId);

  // Get tab from URL query param, default to "overview"
  const tabFromUrl = (searchParams.get("tab") as TabValue) || "overview";
  const [activeTab, setActiveTab] = useState<TabValue>(tabFromUrl);

  // Update tab state when URL changes
  useEffect(() => {
    const tab = (searchParams.get("tab") as TabValue) || "overview";
    if (tab !== activeTab) {
      setActiveTab(tab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Handle tab change - update URL query param
  const handleTabChange = (value: string) => {
    const newTab = value as TabValue;
    setActiveTab(newTab);
    router.push(`/jobs/${jobId}?tab=${newTab}`, { scroll: false });
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">Loading job...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <div className="text-destructive">
          {error ? "Failed to load job" : "Job not found"}
        </div>
        <button
          onClick={() => router.push("/jobs")}
          className="text-sm text-muted-foreground underline"
        >
          Back to Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="resume">Resume</TabsTrigger>
          <TabsTrigger value="cover">Cover Letter</TabsTrigger>
          <TabsTrigger value="notes">Notes</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <OverviewTab job={job} />
        </TabsContent>

        <TabsContent value="resume" className="mt-6">
          <ResumeTab
            jobId={jobId}
            jobDescription={job.job_description || ""}
            jobStatus={job.status}
          />
        </TabsContent>

        <TabsContent value="cover" className="mt-6">
          <CoverLetterTab jobId={jobId} />
        </TabsContent>

        <TabsContent value="notes" className="mt-6">
          <NotesTab jobId={jobId} job={job} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
