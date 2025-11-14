"use client";

import { useParams, usePathname } from "next/navigation";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const steps = [
  { id: 1, name: "Details", path: "details" },
  { id: 2, name: "Experience", path: "experience" },
  { id: 3, name: "Proposals", path: "proposals" },
] as const;

export default function IntakeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const pathname = usePathname();
  const jobId = params.jobId as string;
  
  // Check if this is a new job (not yet created)
  const isNewJob = jobId === "new";

  // Determine current step from pathname
  const currentStep = pathname.includes("/experience")
    ? 2
    : pathname.includes("/proposals")
    ? 3
    : 1;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Progress Indicator */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Step Names */}
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex flex-1 items-center">
                  <div className="flex flex-col items-center">
                    {isNewJob && step.id > 1 ? (
                      // Render disabled step indicator for new jobs
                      <div
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-medium cursor-not-allowed",
                          "border-muted bg-muted text-muted-foreground"
                        )}
                      >
                        {step.id}
                      </div>
                    ) : (
                      // Render clickable link for existing jobs or step 1
                      <Link
                        href={`/intake/${jobId}/${step.path}`}
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-medium transition-colors",
                          currentStep === step.id
                            ? "border-primary bg-primary text-primary-foreground"
                            : currentStep > step.id
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-muted bg-muted text-muted-foreground"
                        )}
                      >
                        {step.id}
                      </Link>
                    )}
                    <span
                      className={cn(
                        "mt-2 text-xs font-medium",
                        currentStep >= step.id && !isNewJob
                          ? "text-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      {step.name}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={cn(
                        "mx-2 h-0.5 flex-1",
                        currentStep > step.id && !isNewJob ? "bg-primary" : "bg-muted"
                      )}
                    />
                  )}
                </div>
              ))}
            </div>

            {/* Progress Bar */}
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ 
                  width: isNewJob 
                    ? "0%" 
                    : `${((currentStep - 1) / (steps.length - 1)) * 100}%` 
                }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Page Content */}
      {children}
    </div>
  );
}

