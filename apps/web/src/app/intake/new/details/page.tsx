"use client";

import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { JobDetailsForm } from "@/components/intake/JobDetailsForm";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { Button } from "@/components/ui/button";

export default function IntakeNewDetailsPage() {
  const router = useRouter();
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();

  const handleJobCreated = (jobId: number) => {
    // Replace URL without adding to history stack
    router.replace(`/intake/${jobId}/details`);
  };

  if (isLoadingUser) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <div className="text-destructive">
          User not found. Please refresh the page.
        </div>
        <Button onClick={() => router.push("/")} variant="outline">
          Back to Home
        </Button>
      </div>
    );
  }

  return <JobDetailsForm mode="create" onJobCreated={handleJobCreated} />;
}

