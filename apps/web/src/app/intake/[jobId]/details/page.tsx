"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useJob } from "@/lib/hooks/useJobs";
import { useUpdateJob } from "@/lib/hooks/useJobMutations";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { useQuery } from "@tanstack/react-query";

const jobDetailsSchema = z.object({
  title: z.string().min(1, "Job title is required"),
  company: z.string().min(1, "Company name is required"),
  description: z.string().min(1, "Job description is required"),
});

type JobDetailsFormData = z.infer<typeof jobDetailsSchema>;

export default function IntakeDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.jobId as string, 10);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { setJobId, setCurrentStep, setJobDetails, setSessionId } =
    useIntakeStore();

  // Fetch job data
  const { data: job, isLoading: isLoadingJob } = useJob(jobId);

  // Fetch or create intake session
  const { data: intakeSession } = useQuery({
    queryKey: ["intake-session", jobId],
    queryFn: () => jobsAPI.getIntakeSession(jobId),
    enabled: !!jobId,
    retry: false,
  });

  // Create intake session if it doesn't exist
  const createSession = async () => {
    try {
      const session = await jobsAPI.createIntakeSession(jobId);
      setSessionId(session.id.toString());
      return session;
    } catch (error) {
      console.error("Failed to create intake session:", error);
      throw error;
    }
  };

  const updateJob = useUpdateJob();

  const form = useForm<JobDetailsFormData>({
    resolver: zodResolver(jobDetailsSchema),
    defaultValues: {
      title: "",
      company: "",
      description: "",
    },
  });

  // Initialize form with job data
  useEffect(() => {
    if (job) {
      form.reset({
        title: job.title || "",
        company: job.company || "",
        description: job.job_description || "",
      });
      setJobId(job.id);
    }
  }, [job, form, setJobId]);

  // Initialize session ID
  useEffect(() => {
    if (intakeSession) {
      setSessionId(intakeSession.id.toString());
    }
  }, [intakeSession, setSessionId]);

  const onSubmit = async (data: JobDetailsFormData) => {
    if (!job) return;

    setIsSubmitting(true);
    try {
      // Update job with details
      await updateJob.mutateAsync({
        jobId: job.id,
        data: {
          title: data.title.trim(),
          company: data.company.trim(),
          job_description: data.description.trim(),
        },
      });

      // Ensure intake session exists
      let session = intakeSession;
      if (!session) {
        session = await createSession();
      }

      // Update session to mark step 1 as completed
      if (session) {
        await jobsAPI.updateIntakeSession(job.id, {
          current_step: 2,
          step_completed: 1,
        });
      }

      // Update Zustand store
      setJobDetails({
        title: data.title.trim(),
        company: data.company.trim(),
        description: data.description.trim(),
      });
      setCurrentStep("experience");

      // Navigate to experience step
      router.push(`/intake/${job.id}/experience`);
    } catch (error) {
      console.error("Failed to save job details:", error);
      // Error will be handled by TanStack Query
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingJob) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">Loading job...</div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <div className="text-destructive">Job not found</div>
        <Button onClick={() => router.push("/jobs")} variant="outline">
          Back to Jobs
        </Button>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Details</CardTitle>
        <CardDescription>
          Enter the job title, company name, and description. This information
          will be used to generate your resume and cover letter.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Job Title</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="e.g., Senior Software Engineer"
                    />
                  </FormControl>
                  <FormDescription>
                    The title of the position you&apos;re applying for.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="company"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Company Name</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="e.g., Acme Corporation" />
                  </FormControl>
                  <FormDescription>
                    The name of the company offering this position.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Job Description</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Enter the full job description, requirements, and any relevant details..."
                      className="min-h-[300px] resize-y"
                    />
                  </FormControl>
                  <FormDescription>
                    Paste the complete job description, including requirements,
                    responsibilities, and preferred qualifications.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push(`/jobs/${job.id}`)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || updateJob.isPending}
              >
                {isSubmitting || updateJob.isPending
                  ? "Saving..."
                  : "Continue to Experience Selection"}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

