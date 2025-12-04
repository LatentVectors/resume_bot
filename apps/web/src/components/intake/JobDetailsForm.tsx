"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Star, Loader2, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useCreateJob, useUpdateJob } from "@/lib/hooks/useJobMutations";
import { useIntakeInitialization } from "@/lib/hooks/useIntakeInitialization";
import { useIntakeStore } from "@/lib/store/intake";
import { langgraphWorkflowsAPI } from "@/lib/api/workflows";
import { toast } from "sonner";
import { IntakeStepHeader } from "@/components/intake/IntakeStepHeader";

const jobDetailsSchema = z.object({
  title: z.string().min(1, "Job title is required"),
  company: z.string().min(1, "Company name is required"),
  description: z.string().min(1, "Job description is required"),
  favorite: z.boolean(),
});

export type JobDetailsFormData = z.infer<typeof jobDetailsSchema>;

interface JobDetailsFormProps {
  mode: "create" | "edit";
  jobId?: number;
  initialData?: JobDetailsFormData;
  onJobCreated?: (jobId: number) => void;
  onComplete?: () => void;
  onCancel?: () => void;
}

export function JobDetailsForm({
  mode,
  jobId,
  initialData,
  onJobCreated,
  onComplete,
  onCancel,
}: JobDetailsFormProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);

  const { data: user } = useCurrentUser();
  const createJob = useCreateJob();
  const updateJob = useUpdateJob();
  const { 
    initializeIntake, 
    isInitializing, 
    statusMessage: initStatusMessage,
    error: initError,
  } = useIntakeInitialization();
  const { setJobId, setCurrentStep, setJobDetails, setSessionId } = useIntakeStore();

  const form = useForm<JobDetailsFormData>({
    resolver: zodResolver(jobDetailsSchema),
    defaultValues: initialData || {
      title: "",
      company: "",
      description: "",
      favorite: false,
    },
  });

  // Update form when initialData changes (for edit mode)
  useEffect(() => {
    if (initialData && mode === "edit") {
      form.reset(initialData);
    }
  }, [initialData, mode, form]);

  const handleParseInfo = async () => {
    const description = form.getValues("description");
    if (!description || description.trim().length === 0) {
      toast.error("Please enter a job description before parsing.");
      return;
    }

    setIsExtracting(true);
    try {
      const result = await langgraphWorkflowsAPI.extractJobDetails({
        job_description: description,
      });

      if (result.title || result.company) {
        if (result.title) {
          form.setValue("title", result.title);
        }
        if (result.company) {
          form.setValue("company", result.company);
        }
        toast.success(
          result.confidence && result.confidence < 0.5
            ? "Extraction confidence is low. Please review and edit the fields."
            : "Job details extracted successfully."
        );
      } else {
        toast.error("Could not extract job details. Please enter manually.");
      }
    } catch (error) {
      console.error("Failed to extract job details:", error);
      toast.error("Could not extract job details. Please enter manually.");
    } finally {
      setIsExtracting(false);
    }
  };

  const onSubmit = async (data: JobDetailsFormData) => {
    if (!user) {
      toast.error("User not found. Please refresh the page.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === "create") {
        // Create new job
        const job = await createJob.mutateAsync({
          user_id: user.id,
          data: {
            job_title: data.title.trim(),
            company_name: data.company.trim(),
            job_description: data.description.trim(),
            is_favorite: data.favorite,
            status: "Saved",
          },
        });

        // Update store
        setJobId(job.id);
        setJobDetails({
          title: data.title.trim(),
          company: data.company.trim(),
          description: data.description.trim(),
        });

        // Initialize intake session with analyses
        try {
          const result = await initializeIntake({
            jobId: job.id,
            userId: user.id,
            jobDescription: data.description.trim(),
          });
          setSessionId(result.sessionId.toString());
        } catch (initError) {
          console.error("Failed to initialize intake:", initError);
          // Still navigate to experience page, but show error
          toast.error("Failed to prepare analyses. Some features may be limited.");
        }

        // Notify parent component
        if (onJobCreated) {
          onJobCreated(job.id);
        }
      } else {
        // Update existing job
        if (!jobId) {
          toast.error("Job ID is required for update.");
          return;
        }

        await updateJob.mutateAsync({
          jobId,
          data: {
            job_title: data.title.trim(),
            company_name: data.company.trim(),
            job_description: data.description.trim(),
            is_favorite: data.favorite,
          },
        });

        // Update store
        setJobDetails({
          title: data.title.trim(),
          company: data.company.trim(),
          description: data.description.trim(),
        });
        setCurrentStep("experience");

        // Notify parent component or navigate
        if (onComplete) {
          onComplete();
        }
      }
    } catch (error) {
      console.error("Failed to save job details:", error);
      toast.error("Failed to save job details. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const watchedTitle = form.watch("title");
  const watchedCompany = form.watch("company");
  const watchedDescription = form.watch("description");

  // Check if form is valid (all required fields have non-empty, non-whitespace values)
  const isFormValid =
    watchedTitle?.trim().length > 0 &&
    watchedCompany?.trim().length > 0 &&
    watchedDescription?.trim().length > 0;

  // Determine button label based on state
  const getButtonLabel = () => {
    if (isInitializing && initStatusMessage) {
      return initStatusMessage;
    }
    if (isSubmitting) {
      return mode === "create" ? "Creating..." : "Saving...";
    }
    return "Next";
  };

  const handleCancel = () => {
    if (mode === "create") {
      router.push("/jobs");
    } else if (jobId) {
      router.push(`/jobs/${jobId}`);
    }
  };

  return (
    <div className="space-y-6">
      <IntakeStepHeader
        step={1}
        subtitle="Job Details"
        leftButtons={
          onCancel
            ? [
                {
                  label: "Cancel",
                  variant: "outline",
                  onClick: onCancel,
                  disabled: isSubmitting || isInitializing,
                },
              ]
            : undefined
        }
        rightButtons={[
          {
            label: getButtonLabel(),
            type: "submit",
            form: "job-details-form",
            disabled: isSubmitting || isExtracting || isInitializing || !isFormValid,
            loading: isSubmitting || isInitializing,
          },
        ]}
      />
      
      {/* Show initialization error if present */}
      {initError && (
        <Alert variant="destructive">
          <AlertDescription>{initError}</AlertDescription>
        </Alert>
      )}
        <Form {...form}>
          <form
            id="job-details-form"
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-6"
          >
            {/* Single row with Job Title, Company Name, Favorite, and Parse */}
            <div className="flex items-start gap-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem className="flex-1">
                    <FormLabel>Job Title</FormLabel>
                    <FormControl>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="relative">
                            <Input
                              {...field}
                              placeholder="e.g., Senior Software Engineer"
                            />
                            <Info className="absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>
                            The title of the position you&apos;re applying for
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="company"
                render={({ field }) => (
                  <FormItem className="flex-1">
                    <FormLabel>Company Name</FormLabel>
                    <FormControl>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="relative">
                            <Input
                              {...field}
                              placeholder="e.g., Acme Corporation"
                            />
                            <Info className="absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>The name of the company offering this position</p>
                        </TooltipContent>
                      </Tooltip>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="favorite"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center space-x-2 space-y-0 self-end pb-2">
                    <FormControl>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            type="button"
                            onClick={() => field.onChange(!field.value)}
                            className="focus:outline-none"
                          >
                            <Star
                              className={`size-6 ${
                                field.value
                                  ? "fill-yellow-400 text-yellow-400"
                                  : "text-muted-foreground"
                              }`}
                            />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Mark this job as favorite for easy access</p>
                        </TooltipContent>
                      </Tooltip>
                    </FormControl>
                  </FormItem>
                )}
              />
              <div className="self-end">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleParseInfo}
                      disabled={
                        isExtracting ||
                        !watchedDescription ||
                        watchedDescription.trim().length === 0
                      }
                    >
                      {isExtracting ? (
                        <>
                          <Loader2 className="mr-2 size-4 animate-spin" />
                          Parsing...
                        </>
                      ) : (
                        "Parse"
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>
                      Automatically extract job title and company name from the
                      job description below
                    </p>
                  </TooltipContent>
                </Tooltip>
              </div>
            </div>

            {/* Job Description */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Job Description</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Paste the full job description here..."
                      className="h-[250px] resize-none overflow-y-auto"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>
    </div>
  );
}
