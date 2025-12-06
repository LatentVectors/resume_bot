"use client";

import type { ReactNode } from "react";
import { ChevronDown, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type {
  ResumeData,
  ResumeExperience,
  ResumeEducation,
  ResumeCertification,
} from "@resume/database/types";

// Re-export types for backwards compatibility
export type { ResumeData, ResumeExperience, ResumeEducation, ResumeCertification };

interface ResumeEditorProps {
  resumeData: ResumeData;
  updateResume: (updater: (prev: ResumeData) => ResumeData) => void;
  readOnly?: boolean;
}

export function ResumeEditor({ resumeData, updateResume, readOnly = false }: ResumeEditorProps) {
  return (
    <div className="space-y-4">
      <ExpandableSection title="Profile" description="Key personal details">
        <ProfileSection resumeData={resumeData} updateResume={updateResume} readOnly={readOnly} />
      </ExpandableSection>
      <ExpandableSection title="Experience" description="Chronicle your past roles">
        <ExperienceSection resumeData={resumeData} updateResume={updateResume} readOnly={readOnly} />
      </ExpandableSection>
      <ExpandableSection title="Education" description="Academic background">
        <EducationSection resumeData={resumeData} updateResume={updateResume} readOnly={readOnly} />
      </ExpandableSection>
      <ExpandableSection title="Certifications" description="Certifications and licenses">
        <CertificationsSection resumeData={resumeData} updateResume={updateResume} readOnly={readOnly} />
      </ExpandableSection>
      <ExpandableSection title="Skills" description="Tools and proficiencies">
        <SkillsSection resumeData={resumeData} updateResume={updateResume} readOnly={readOnly} />
      </ExpandableSection>
    </div>
  );
}

interface ExpandableSectionProps {
  title: string;
  description?: string;
  open?: boolean;
  children: ReactNode;
}

function ExpandableSection({ title, description, open = true, children }: ExpandableSectionProps) {
  return (
    <details
      open={open}
      className="group cursor-pointer rounded-lg border border-border bg-card"
    >
      <summary className="flex items-center justify-between gap-4 px-4 py-3 text-sm font-semibold list-none text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <div>
          <span className="font-semibold">{title}</span>
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>
        <ChevronDown className="size-4 transition-transform duration-150 group-open:-rotate-180" />
      </summary>
      <div className="border-t border-border px-4 py-4">{children}</div>
    </details>
  );
}

interface SectionProps {
  resumeData: ResumeData;
  updateResume: (updater: (prev: ResumeData) => ResumeData) => void;
  readOnly: boolean;
}

function ProfileSection({ resumeData, updateResume, readOnly }: SectionProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <Label htmlFor="name">Name *</Label>
          <Input
            id="name"
            value={resumeData.name || ""}
            onChange={(e) => updateResume((prev) => ({ ...prev, name: e.target.value }))}
            disabled={readOnly}
          />
        </div>
        <div>
          <Label htmlFor="title">
            Title <span className="text-muted-foreground">(AI-editable)</span>
          </Label>
          <Input
            id="title"
            value={resumeData.title || ""}
            onChange={(e) => updateResume((prev) => ({ ...prev, title: e.target.value }))}
            disabled={readOnly}
          />
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <Label htmlFor="email">Email *</Label>
          <Input
            id="email"
            type="email"
            value={resumeData.email || ""}
            onChange={(e) => updateResume((prev) => ({ ...prev, email: e.target.value }))}
            disabled={readOnly}
          />
        </div>
        <div>
          <Label htmlFor="phone">Phone</Label>
          <Input
            id="phone"
            value={resumeData.phone || ""}
            onChange={(e) => updateResume((prev) => ({ ...prev, phone: e.target.value }))}
            disabled={readOnly}
          />
        </div>
      </div>
      <div>
        <Label htmlFor="linkedin">LinkedIn URL</Label>
        <Input
          id="linkedin"
          value={resumeData.linkedin_url || ""}
          onChange={(e) => updateResume((prev) => ({ ...prev, linkedin_url: e.target.value }))}
          disabled={readOnly}
        />
      </div>
      <div>
        <Label htmlFor="summary">
          Professional Summary <span className="text-muted-foreground">(AI-editable)</span>
        </Label>
        <Textarea
          id="summary"
          value={resumeData.professional_summary || ""}
          onChange={(e) => updateResume((prev) => ({ ...prev, professional_summary: e.target.value }))}
          disabled={readOnly}
          className="min-h-[125px]"
        />
      </div>
    </div>
  );
}

function ExperienceSection({ resumeData, updateResume, readOnly }: SectionProps) {
  const updateExperience = (index: number, updater: (exp: ResumeExperience) => ResumeExperience) => {
    updateResume((prev) => ({
      ...prev,
      experience: prev.experience?.map((exp, i) => (i === index ? updater(exp) : exp)) || [],
    }));
  };

  const deleteExperience = (index: number) => {
    updateResume((prev) => ({
      ...prev,
      experience: prev.experience?.filter((_, i) => i !== index) || [],
    }));
  };

  const addExperience = () => {
    updateResume((prev) => ({
      ...prev,
      experience: [
        ...(prev.experience || []),
        {
          title: "",
          company: "",
          location: "",
          start_date: "",
          end_date: null,
          points: [],
        },
      ],
    }));
  };

  return (
    <div className="space-y-4">
      {(resumeData.experience || []).map((exp, idx) => (
        <Card key={idx} className="p-4">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Title</Label>
                    <Input
                      value={exp.title || ""}
                      onChange={(e) => updateExperience(idx, (prev) => ({ ...prev, title: e.target.value }))}
                      disabled={readOnly}
                    />
                  </div>
                  <div>
                    <Label>Company</Label>
                    <Input
                      value={exp.company || ""}
                      onChange={(e) => updateExperience(idx, (prev) => ({ ...prev, company: e.target.value }))}
                      disabled={readOnly}
                    />
                  </div>
                </div>
                <div>
                  <Label>Location</Label>
                  <Input
                    value={exp.location || ""}
                    onChange={(e) => updateExperience(idx, (prev) => ({ ...prev, location: e.target.value }))}
                    disabled={readOnly}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Start Date</Label>
                    <Input
                      type="date"
                      value={exp.start_date || ""}
                      onChange={(e) => updateExperience(idx, (prev) => ({ ...prev, start_date: e.target.value }))}
                      disabled={readOnly}
                    />
                  </div>
                  <div>
                    <Label>End Date</Label>
                    <Input
                      type="date"
                      value={exp.end_date || ""}
                      onChange={(e) => updateExperience(idx, (prev) => ({ ...prev, end_date: e.target.value || null }))}
                      disabled={readOnly}
                    />
                  </div>
                </div>
                <div>
                  <Label>
                    Points <span className="text-muted-foreground">(AI-editable, one per line)</span>
                  </Label>
                  <Textarea
                    value={(exp.points || []).join("\n")}
                    onChange={(e) =>
                      updateExperience(idx, (prev) => ({
                        ...prev,
                        points: e.target.value.split("\n").filter((p) => p.trim() !== ""),
                      }))
                    }
                    disabled={readOnly}
                    className="min-h-[175px]"
                  />
                </div>
              </div>
              {!readOnly && (
                <Button variant="ghost" size="sm" onClick={() => deleteExperience(idx)} className="ml-4">
                  <Trash2 className="size-4" />
                </Button>
              )}
            </div>
          </div>
        </Card>
      ))}
      {!readOnly && (
        <Button variant="outline" onClick={addExperience}>
          <Plus className="mr-2 size-4" />
          Add Experience
        </Button>
      )}
    </div>
  );
}

function EducationSection({ resumeData, updateResume, readOnly }: SectionProps) {
  const updateEducation = (index: number, updater: (edu: ResumeEducation) => ResumeEducation) => {
    updateResume((prev) => ({
      ...prev,
      education: prev.education?.map((edu, i) => (i === index ? updater(edu) : edu)) || [],
    }));
  };

  const deleteEducation = (index: number) => {
    updateResume((prev) => ({
      ...prev,
      education: prev.education?.filter((_, i) => i !== index) || [],
    }));
  };

  const addEducation = () => {
    updateResume((prev) => ({
      ...prev,
      education: [
        ...(prev.education || []),
        {
          degree: "",
          major: "",
          institution: "",
          grad_date: "",
        },
      ],
    }));
  };

  return (
    <div className="space-y-4">
      {(resumeData.education || []).map((edu, idx) => (
        <Card key={idx} className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 space-y-4">
              <div>
                <Label>Institution</Label>
                <Input
                  value={edu.institution || ""}
                  onChange={(e) => updateEducation(idx, (prev) => ({ ...prev, institution: e.target.value }))}
                  disabled={readOnly}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Degree</Label>
                  <Input
                    value={edu.degree || ""}
                    onChange={(e) => updateEducation(idx, (prev) => ({ ...prev, degree: e.target.value }))}
                    disabled={readOnly}
                  />
                </div>
                <div>
                  <Label>Major</Label>
                  <Input
                    value={edu.major || ""}
                    onChange={(e) => updateEducation(idx, (prev) => ({ ...prev, major: e.target.value }))}
                    disabled={readOnly}
                  />
                </div>
              </div>
              <div>
                <Label>Graduation Date</Label>
                <Input
                  type="date"
                  value={edu.grad_date || ""}
                  onChange={(e) => updateEducation(idx, (prev) => ({ ...prev, grad_date: e.target.value }))}
                  disabled={readOnly}
                />
              </div>
            </div>
            {!readOnly && (
              <Button variant="ghost" size="sm" onClick={() => deleteEducation(idx)} className="ml-4">
                <Trash2 className="size-4" />
              </Button>
            )}
          </div>
        </Card>
      ))}
      {!readOnly && (
        <Button variant="outline" onClick={addEducation}>
          <Plus className="mr-2 size-4" />
          Add Education
        </Button>
      )}
    </div>
  );
}

function CertificationsSection({ resumeData, updateResume, readOnly }: SectionProps) {
  const updateCertification = (index: number, updater: (cert: ResumeCertification) => ResumeCertification) => {
    updateResume((prev) => ({
      ...prev,
      certifications: prev.certifications?.map((cert, i) => (i === index ? updater(cert) : cert)) || [],
    }));
  };

  const deleteCertification = (index: number) => {
    updateResume((prev) => ({
      ...prev,
      certifications: prev.certifications?.filter((_, i) => i !== index) || [],
    }));
  };

  const addCertification = () => {
    updateResume((prev) => ({
      ...prev,
      certifications: [
        ...(prev.certifications || []),
        {
          title: "",
          date: "",
        },
      ],
    }));
  };

  return (
    <div className="space-y-4">
      {(resumeData.certifications || []).map((cert, idx) => (
        <Card key={idx} className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 space-y-4">
              <div>
                <Label>Title</Label>
                <Input
                  value={cert.title || ""}
                  onChange={(e) => updateCertification(idx, (prev) => ({ ...prev, title: e.target.value }))}
                  disabled={readOnly}
                />
              </div>
              <div>
                <Label>Date</Label>
                <Input
                  type="date"
                  value={cert.date || ""}
                  onChange={(e) => updateCertification(idx, (prev) => ({ ...prev, date: e.target.value }))}
                  disabled={readOnly}
                />
              </div>
            </div>
            {!readOnly && (
              <Button variant="ghost" size="sm" onClick={() => deleteCertification(idx)} className="ml-4">
                <Trash2 className="size-4" />
              </Button>
            )}
          </div>
        </Card>
      ))}
      {!readOnly && (
        <Button variant="outline" onClick={addCertification}>
          <Plus className="mr-2 size-4" />
          Add Certification
        </Button>
      )}
    </div>
  );
}

function SkillsSection({ resumeData, updateResume, readOnly }: SectionProps) {
  const skillsText = (resumeData.skills || []).join("\n");

  return (
    <div>
      <Label htmlFor="skills">
        Skills <span className="text-muted-foreground">(AI-editable, one per line or comma-separated)</span>
      </Label>
      <Textarea
        id="skills"
        value={skillsText}
        onChange={(e) => {
          const text = e.target.value;
          const skills = text
            .split(/[,\n]/)
            .map((s) => s.trim())
            .filter((s) => s !== "");
          updateResume((prev) => ({ ...prev, skills }));
        }}
        disabled={readOnly}
        className="mt-2 min-h-[200px]"
        placeholder="Enter skills, one per line or comma-separated..."
      />
    </div>
  );
}
