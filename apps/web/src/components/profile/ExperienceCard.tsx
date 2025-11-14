"use client";

import { useState } from "react";
import { Edit, Trash2, Plus, ChevronDown, ChevronUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useExperiences } from "@/lib/hooks/useExperiences";
import {
  useCreateExperience,
  useUpdateExperience,
  useDeleteExperience,
} from "@/lib/hooks/useExperienceMutations";
import { useAchievements } from "@/lib/hooks/useAchievements";
import {
  useCreateAchievement,
  useUpdateAchievement,
  useDeleteAchievement,
} from "@/lib/hooks/useExperienceMutations";
import type { components } from "@/types/api";

type ExperienceResponse = components["schemas"]["ExperienceResponse"];
type AchievementResponse = components["schemas"]["AchievementResponse"];

const experienceSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  job_title: z.string().min(1, "Job title is required"),
  location: z.string().optional(),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().optional(),
  company_overview: z.string().optional(),
  role_overview: z.string().optional(),
  skills: z.string().optional(),
});

const achievementSchema = z.object({
  title: z.string().min(1, "Title is required"),
  content: z.string().min(1, "Content is required"),
});

type ExperienceFormData = z.infer<typeof experienceSchema>;
type AchievementFormData = z.infer<typeof achievementSchema>;

interface ExperienceCardProps {
  experience: ExperienceResponse;
  userId: number;
}

export function ExperienceCard({ experience, userId }: ExperienceCardProps) {
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAchievements, setShowAchievements] = useState(false);
  const [showAddAchievementDialog, setShowAddAchievementDialog] = useState(false);
  const [editingAchievement, setEditingAchievement] = useState<AchievementResponse | null>(null);

  const updateExperience = useUpdateExperience();
  const deleteExperience = useDeleteExperience();
  const { data: achievements } = useAchievements(experience.id);
  const createAchievement = useCreateAchievement();
  const updateAchievement = useUpdateAchievement();
  const deleteAchievement = useDeleteAchievement();

  const form = useForm<ExperienceFormData>({
    resolver: zodResolver(experienceSchema),
    defaultValues: {
      company_name: experience.company_name,
      job_title: experience.job_title,
      location: experience.location || "",
      start_date: experience.start_date,
      end_date: experience.end_date || "",
      company_overview: experience.company_overview || "",
      role_overview: experience.role_overview || "",
      skills: experience.skills?.join(", ") || "",
    },
  });

  const achievementForm = useForm<AchievementFormData>({
    resolver: zodResolver(achievementSchema),
    defaultValues: {
      title: "",
      content: "",
    },
  });

  const onEditSubmit = async (data: ExperienceFormData) => {
    try {
      await updateExperience.mutateAsync({
        experienceId: experience.id,
        data: {
          company_name: data.company_name,
          job_title: data.job_title,
          location: data.location || null,
          start_date: data.start_date,
          end_date: data.end_date || null,
          company_overview: data.company_overview || null,
          role_overview: data.role_overview || null,
          skills: data.skills
            ? data.skills.split(",").map((s) => s.trim()).filter(Boolean)
            : null,
        },
      });
      setShowEditDialog(false);
    } catch (error) {
      console.error("Failed to update experience:", error);
    }
  };

  const onDelete = async () => {
    try {
      await deleteExperience.mutateAsync(experience.id);
      setShowDeleteDialog(false);
    } catch (error) {
      console.error("Failed to delete experience:", error);
    }
  };

  const onAchievementSubmit = async (data: AchievementFormData) => {
    try {
      if (editingAchievement) {
        await updateAchievement.mutateAsync({
          achievementId: editingAchievement.id,
          data: {
            title: data.title,
            content: data.content,
          },
        });
        setEditingAchievement(null);
      } else {
        await createAchievement.mutateAsync({
          experienceId: experience.id,
          data: {
            title: data.title,
            content: data.content,
            order: achievements?.length || 0,
          },
        });
        setShowAddAchievementDialog(false);
      }
      achievementForm.reset();
    } catch (error) {
      console.error("Failed to save achievement:", error);
    }
  };

  const onDeleteAchievement = async (achievementId: number) => {
    try {
      await deleteAchievement.mutateAsync(achievementId);
    } catch (error) {
      console.error("Failed to delete achievement:", error);
    }
  };

  const startEditAchievement = (achievement: AchievementResponse) => {
    setEditingAchievement(achievement);
    achievementForm.reset({
      title: achievement.title,
      content: achievement.content,
    });
    setShowAddAchievementDialog(true);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Present";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
    });
  };

  const sortedAchievements = achievements
    ? [...achievements].sort((a, b) => a.order - b.order)
    : [];

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle>{experience.job_title}</CardTitle>
              <CardDescription>{experience.company_name}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowEditDialog(true)}
              >
                <Edit className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive hover:text-destructive"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">
            <div>
              {formatDate(experience.start_date)} - {formatDate(experience.end_date)}
            </div>
            {experience.location && <div>{experience.location}</div>}
          </div>

          {experience.role_overview && (
            <p className="text-sm">{experience.role_overview}</p>
          )}

          {experience.skills && experience.skills.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {experience.skills.map((skill, idx) => (
                <Badge key={idx} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          )}

          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium">Achievements</h4>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingAchievement(null);
                    achievementForm.reset();
                    setShowAddAchievementDialog(true);
                  }}
                >
                  <Plus className="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAchievements(!showAchievements)}
                >
                  {showAchievements ? (
                    <ChevronUp className="size-4" />
                  ) : (
                    <ChevronDown className="size-4" />
                  )}
                </Button>
              </div>
            </div>
            {showAchievements && (
              <div className="space-y-2">
                {sortedAchievements.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No achievements yet</p>
                ) : (
                  sortedAchievements.map((achievement) => (
                    <div
                      key={achievement.id}
                      className="flex items-start justify-between rounded-md border p-3"
                    >
                      <div className="flex-1">
                        <div className="font-medium text-sm">{achievement.title}</div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {achievement.content}
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => startEditAchievement(achievement)}
                        >
                          <Edit className="size-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={() => onDeleteAchievement(achievement.id)}
                        >
                          <Trash2 className="size-3" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Edit Experience Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Experience</DialogTitle>
            <DialogDescription>
              Update your work experience details.
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onEditSubmit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="company_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Company Name *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="job_title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Job Title *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="location"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Location</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="start_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Start Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="end_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>End Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormDescription>Leave empty for current position</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="company_overview"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Company Overview</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="role_overview"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role Overview</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="skills"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Skills</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="e.g., Python, SQL, Project Management" />
                    </FormControl>
                    <FormDescription>Separate skills with commas</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowEditDialog(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={updateExperience.isPending}>
                  {updateExperience.isPending ? "Saving..." : "Save"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Delete Experience Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Experience</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this experience? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleteExperience.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={onDelete}
              disabled={deleteExperience.isPending}
            >
              {deleteExperience.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Achievement Dialog */}
      <Dialog open={showAddAchievementDialog} onOpenChange={setShowAddAchievementDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingAchievement ? "Edit Achievement" : "Add Achievement"}
            </DialogTitle>
            <DialogDescription>
              {editingAchievement
                ? "Update achievement details."
                : "Add a new achievement for this experience."}
            </DialogDescription>
          </DialogHeader>
          <Form {...achievementForm}>
            <form
              onSubmit={achievementForm.handleSubmit(onAchievementSubmit)}
              className="space-y-4"
            >
              <FormField
                control={achievementForm.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Title *</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={achievementForm.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Content *</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={4} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowAddAchievementDialog(false);
                    setEditingAchievement(null);
                    achievementForm.reset();
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createAchievement.isPending || updateAchievement.isPending}
                >
                  {createAchievement.isPending || updateAchievement.isPending
                    ? "Saving..."
                    : editingAchievement
                      ? "Update"
                      : "Add"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </>
  );
}

