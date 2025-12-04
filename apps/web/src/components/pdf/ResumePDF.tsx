/**
 * Resume PDF Document Component
 *
 * Renders a professional resume PDF using @react-pdf/renderer.
 * This component is designed for client-side PDF generation.
 */

import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Link,
} from "@react-pdf/renderer";
import type {
  ResumeData,
  ResumeExperience,
  ResumeEducation,
  ResumeCertification,
} from "@resume/database/types";

// Color palette
const colors = {
  primary: "#1a1a1a",
  secondary: "#4a4a4a",
  accent: "#2563eb",
  muted: "#6b7280",
  border: "#e5e7eb",
};

// Professional resume styles
const styles = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 10,
    paddingTop: 36,
    paddingBottom: 36,
    paddingHorizontal: 40,
    color: colors.primary,
  },
  // Header section
  header: {
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 12,
  },
  name: {
    fontSize: 22,
    fontFamily: "Helvetica-Bold",
    marginBottom: 4,
    color: colors.primary,
  },
  title: {
    fontSize: 12,
    color: colors.accent,
    marginBottom: 8,
  },
  contactRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  contactItem: {
    fontSize: 9,
    color: colors.secondary,
  },
  link: {
    color: colors.accent,
    textDecoration: "none",
  },
  // Section styles
  section: {
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    color: colors.primary,
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 4,
  },
  // Summary
  summary: {
    fontSize: 10,
    lineHeight: 1.5,
    color: colors.secondary,
    textAlign: "justify",
  },
  // Experience
  experienceItem: {
    marginBottom: 10,
  },
  experienceHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 2,
  },
  experienceTitle: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    color: colors.primary,
  },
  experienceCompany: {
    fontSize: 10,
    color: colors.secondary,
    marginBottom: 2,
  },
  experienceDate: {
    fontSize: 9,
    color: colors.muted,
  },
  experienceLocation: {
    fontSize: 9,
    color: colors.muted,
    marginBottom: 4,
  },
  bulletList: {
    marginTop: 4,
  },
  bulletItem: {
    flexDirection: "row",
    marginBottom: 3,
  },
  bullet: {
    width: 10,
    fontSize: 9,
    color: colors.secondary,
  },
  bulletText: {
    flex: 1,
    fontSize: 9,
    lineHeight: 1.4,
    color: colors.secondary,
  },
  // Education
  educationItem: {
    marginBottom: 8,
  },
  educationHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 2,
  },
  educationInstitution: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    color: colors.primary,
  },
  educationDegree: {
    fontSize: 9,
    color: colors.secondary,
  },
  educationDate: {
    fontSize: 9,
    color: colors.muted,
  },
  // Certifications
  certificationItem: {
    marginBottom: 4,
  },
  certificationTitle: {
    fontSize: 10,
    color: colors.primary,
  },
  certificationOrg: {
    fontSize: 9,
    color: colors.muted,
  },
  // Skills
  skillsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  skillItem: {
    fontSize: 9,
    color: colors.secondary,
    backgroundColor: "#f3f4f6",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 3,
  },
});

// Helper to format dates
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "Present";
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

// Header Component
function Header({ data }: { data: ResumeData }) {
  const contactItems: React.ReactNode[] = [];

  if (data.email) {
    contactItems.push(
      <Link key="email" src={`mailto:${data.email}`} style={styles.link}>
        <Text style={styles.contactItem}>{data.email}</Text>
      </Link>
    );
  }

  if (data.phone) {
    contactItems.push(
      <Text key="phone" style={styles.contactItem}>
        {data.phone}
      </Text>
    );
  }

  if (data.location) {
    contactItems.push(
      <Text key="location" style={styles.contactItem}>
        {data.location}
      </Text>
    );
  }

  if (data.linkedin_url) {
    // Clean up LinkedIn URL for display
    const displayUrl = data.linkedin_url
      .replace("https://", "")
      .replace("http://", "")
      .replace("www.", "");
    contactItems.push(
      <Link key="linkedin" src={data.linkedin_url} style={styles.link}>
        <Text style={styles.contactItem}>{displayUrl}</Text>
      </Link>
    );
  }

  return (
    <View style={styles.header}>
      {data.name && <Text style={styles.name}>{data.name}</Text>}
      {data.title && <Text style={styles.title}>{data.title}</Text>}
      {contactItems.length > 0 && (
        <View style={styles.contactRow}>
          {contactItems.map((item, index) => (
            <View key={index}>{item}</View>
          ))}
        </View>
      )}
    </View>
  );
}

// Summary Section
function SummarySection({ summary }: { summary: string }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Professional Summary</Text>
      <Text style={styles.summary}>{summary}</Text>
    </View>
  );
}

// Experience Section
function ExperienceSection({ experiences }: { experiences: ResumeExperience[] }) {
  if (!experiences || experiences.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Experience</Text>
      {experiences.map((exp, index) => (
        <View key={index} style={styles.experienceItem}>
          <View style={styles.experienceHeader}>
            <Text style={styles.experienceTitle}>{exp.title}</Text>
            <Text style={styles.experienceDate}>
              {formatDate(exp.start_date)} – {formatDate(exp.end_date)}
            </Text>
          </View>
          <Text style={styles.experienceCompany}>{exp.company}</Text>
          {exp.location && (
            <Text style={styles.experienceLocation}>{exp.location}</Text>
          )}
          {exp.points && exp.points.length > 0 && (
            <View style={styles.bulletList}>
              {exp.points.map((point, pointIndex) => (
                <View key={pointIndex} style={styles.bulletItem}>
                  <Text style={styles.bullet}>•</Text>
                  <Text style={styles.bulletText}>{point}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      ))}
    </View>
  );
}

// Education Section
function EducationSection({ education }: { education: ResumeEducation[] }) {
  if (!education || education.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Education</Text>
      {education.map((edu, index) => (
        <View key={index} style={styles.educationItem}>
          <View style={styles.educationHeader}>
            <Text style={styles.educationInstitution}>{edu.institution}</Text>
            {edu.grad_date && (
              <Text style={styles.educationDate}>{formatDate(edu.grad_date)}</Text>
            )}
          </View>
          <Text style={styles.educationDegree}>
            {edu.degree}
            {edu.major ? `, ${edu.major}` : ""}
            {edu.gpa ? ` • GPA: ${edu.gpa}` : ""}
          </Text>
        </View>
      ))}
    </View>
  );
}

// Certifications Section
function CertificationsSection({
  certifications,
}: {
  certifications: ResumeCertification[];
}) {
  if (!certifications || certifications.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Certifications</Text>
      {certifications.map((cert, index) => (
        <View key={index} style={styles.certificationItem}>
          <Text style={styles.certificationTitle}>
            {cert.title}
            {cert.date ? ` (${formatDate(cert.date)})` : ""}
          </Text>
          {cert.issuing_organization && (
            <Text style={styles.certificationOrg}>
              {cert.issuing_organization}
            </Text>
          )}
        </View>
      ))}
    </View>
  );
}

// Skills Section
function SkillsSection({ skills }: { skills: string[] }) {
  if (!skills || skills.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Skills</Text>
      <View style={styles.skillsContainer}>
        {skills.map((skill, index) => (
          <Text key={index} style={styles.skillItem}>
            {skill}
          </Text>
        ))}
      </View>
    </View>
  );
}

// Main Resume PDF Document
interface ResumePDFProps {
  data: ResumeData;
}

export function ResumePDF({ data }: ResumePDFProps) {
  return (
    <Document>
      <Page size="LETTER" style={styles.page}>
        <Header data={data} />

        {data.professional_summary && (
          <SummarySection summary={data.professional_summary} />
        )}

        {data.experience && data.experience.length > 0 && (
          <ExperienceSection experiences={data.experience} />
        )}

        {data.education && data.education.length > 0 && (
          <EducationSection education={data.education} />
        )}

        {data.certifications && data.certifications.length > 0 && (
          <CertificationsSection certifications={data.certifications} />
        )}

        {data.skills && data.skills.length > 0 && (
          <SkillsSection skills={data.skills} />
        )}
      </Page>
    </Document>
  );
}

export default ResumePDF;

