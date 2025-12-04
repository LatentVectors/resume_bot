"use client";

import { useState } from "react";
import { Edit, Trash2, Plus, ChevronDown, ChevronUp } from "lucide-react";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";

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
import type { Experience, Achievement as AchievementType } from "@resume/database/types";

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
  experience: Experience;
  userId: number;
}

export function ExperienceCard({ experience, userId }: ExperienceCardProps) {
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAddAchievementDialog, setShowAddAchievementDialog] =
    useState(false);
  const [editingAchievement, setEditingAchievement] =
    useState<AchievementType | null>(null);
  const [deletingAchievementId, setDeletingAchievementId] = useState<
    number | null
  >(null);
  const [expandedCompanyOverview, setExpandedCompanyOverview] = useState(false);
  const [expandedRoleOverview, setExpandedRoleOverview] = useState(false);
  const [expandedAchievements, setExpandedAchievements] = useState<Set<number>>(
    new Set()
  );

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
            ? data.skills
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean)
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
      setDeletingAchievementId(null);
    } catch (error) {
      console.error("Failed to delete achievement:", error);
      setDeletingAchievementId(null);
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + "...";
  };

  const startEditAchievement = (achievement: AchievementType) => {
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
              <CardDescription className="mt-1">
                {experience.company_name}
              </CardDescription>
              <div className="text-xs text-muted-foreground mt-1">
                {formatDate(experience.start_date)} -{" "}
                {formatDate(experience.end_date)}
                {experience.location && ` • ${experience.location}`}
              </div>
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
        <CardContent className="space-y-3">
          {experience.company_overview && (
            <div className="text-sm space-y-1">
              <h5 className="font-medium text-sm">Company Overview</h5>
              <p className="text-muted-foreground">
                {expandedCompanyOverview ||
                experience.company_overview.length <= 300
                  ? experience.company_overview
                  : truncateText(experience.company_overview, 300)}
                {experience.company_overview.length > 300 && (
                  <button
                    onClick={() =>
                      setExpandedCompanyOverview(!expandedCompanyOverview)
                    }
                    className="ml-1 text-primary hover:underline"
                  >
                    {expandedCompanyOverview ? "show less" : "show more"}
                  </button>
                )}
              </p>
            </div>
          )}

          {experience.role_overview && (
            <div className="text-sm space-y-1">
              <h5 className="font-medium text-sm">Role Overview</h5>
              <p className="text-muted-foreground">
                {expandedRoleOverview || experience.role_overview.length <= 300
                  ? experience.role_overview
                  : truncateText(experience.role_overview, 300)}
                {experience.role_overview.length > 300 && (
                  <button
                    onClick={() =>
                      setExpandedRoleOverview(!expandedRoleOverview)
                    }
                    className="ml-1 text-primary hover:underline"
                  >
                    {expandedRoleOverview ? "show less" : "show more"}
                  </button>
                )}
              </p>
            </div>
          )}

          {experience.skills && experience.skills.length > 0 && (
            <div className="text-sm space-y-1">
              <h5 className="font-medium text-sm">Skills</h5>
              <div className="flex flex-wrap gap-2">
                {experience.skills.map((skill, idx) => (
                  <Badge key={idx} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="border-t pt-3">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium">
                Achievements ({sortedAchievements.length})
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingAchievement(null);
                  achievementForm.reset();
                  setShowAddAchievementDialog(true);
                }}
              >
                <Plus className="mr-2 size-4" />
                Add Achievement
              </Button>
            </div>
            <div className="space-y-2">
              {sortedAchievements.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No achievements yet
                </p>
              ) : (
                sortedAchievements.map((achievement) => {
                  const isExpanded = expandedAchievements.has(achievement.id);
                  return (
                    <div
                      key={achievement.id}
                      className="border rounded-md overflow-hidden"
                    >
                      <div
                        onClick={() => {
                          const newExpanded = new Set(expandedAchievements);
                          if (isExpanded) {
                            newExpanded.delete(achievement.id);
                          } else {
                            newExpanded.add(achievement.id);
                          }
                          setExpandedAchievements(newExpanded);
                        }}
                        className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors cursor-pointer"
                      >
                        <div className="font-medium text-sm flex-1 text-left">
                          {achievement.title}
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              startEditAchievement(achievement);
                            }}
                            className="h-7 w-7 p-0"
                          >
                            <Edit className="size-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive h-7 w-7 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeletingAchievementId(achievement.id);
                            }}
                          >
                            <Trash2 className="size-3" />
                          </Button>
                          {isExpanded ? (
                            <ChevronUp className="size-4 ml-1" />
                          ) : (
                            <ChevronDown className="size-4 ml-1" />
                          )}
                        </div>
                      </div>
                      {isExpanded && (
                        <div className="px-3 pb-3 text-sm text-muted-foreground">
                          {achievement.content}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit Experience Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Experience</DialogTitle>
            <DialogDescription>
              Update your work experience details.
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onEditSubmit)}
              className="space-y-4"
            >
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
                      <FormDescription>
                        Leave empty for current position
                      </FormDescription>
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
                      <Input
                        {...field}
                        placeholder="e.g., Python, SQL, Project Management"
                      />
                    </FormControl>
                    <FormDescription>
                      Separate skills with commas
                    </FormDescription>
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
      <DeleteConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={onDelete}
        itemName={`${experience.job_title} at ${experience.company_name}`}
        itemType="Experience"
        isDeleting={deleteExperience.isPending}
      />

      {/* Add/Edit Achievement Dialog */}
      <Dialog
        open={showAddAchievementDialog}
        onOpenChange={setShowAddAchievementDialog}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
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
                      <Textarea {...field} rows={25} />
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
                  disabled={
                    createAchievement.isPending || updateAchievement.isPending
                  }
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

      {/* Delete Achievement Dialog */}
      {deletingAchievementId !== null && (
        <DeleteConfirmationDialog
          open={deletingAchievementId !== null}
          onOpenChange={(open) => {
            if (!open) setDeletingAchievementId(null);
          }}
          onConfirm={() => {
            if (deletingAchievementId !== null) {
              onDeleteAchievement(deletingAchievementId);
            }
          }}
          itemName={
            sortedAchievements.find((a) => a.id === deletingAchievementId)
              ?.title || "Achievement"
          }
          itemType="Achievement"
          isDeleting={deleteAchievement.isPending}
        />
      )}
    </>
  );
}
