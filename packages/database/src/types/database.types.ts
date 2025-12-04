export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      achievements: {
        Row: {
          content: string
          created_at: string
          experience_id: number
          id: number
          order: number
          title: string
          updated_at: string
        }
        Insert: {
          content: string
          created_at?: string
          experience_id: number
          id?: number
          order?: number
          title: string
          updated_at?: string
        }
        Update: {
          content?: string
          created_at?: string
          experience_id?: number
          id?: number
          order?: number
          title?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "achievements_experience_id_fkey"
            columns: ["experience_id"]
            isOneToOne: false
            referencedRelation: "experiences"
            referencedColumns: ["id"]
          },
        ]
      }
      certifications: {
        Row: {
          created_at: string
          date: string
          id: number
          institution: string | null
          title: string
          updated_at: string
          user_id: number
        }
        Insert: {
          created_at?: string
          date: string
          id?: number
          institution?: string | null
          title: string
          updated_at?: string
          user_id: number
        }
        Update: {
          created_at?: string
          date?: string
          id?: number
          institution?: string | null
          title?: string
          updated_at?: string
          user_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "certifications_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      cover_letter_versions: {
        Row: {
          cover_letter_id: number
          cover_letter_json: string
          created_at: string
          created_by_user_id: number
          id: number
          job_id: number
          template_name: string
          version_index: number
        }
        Insert: {
          cover_letter_id: number
          cover_letter_json: string
          created_at?: string
          created_by_user_id: number
          id?: number
          job_id: number
          template_name: string
          version_index: number
        }
        Update: {
          cover_letter_id?: number
          cover_letter_json?: string
          created_at?: string
          created_by_user_id?: number
          id?: number
          job_id?: number
          template_name?: string
          version_index?: number
        }
        Relationships: [
          {
            foreignKeyName: "cover_letter_versions_cover_letter_id_fkey"
            columns: ["cover_letter_id"]
            isOneToOne: false
            referencedRelation: "cover_letters"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "cover_letter_versions_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: false
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      cover_letters: {
        Row: {
          cover_letter_json: string
          created_at: string
          id: number
          job_id: number
          locked: boolean
          template_name: string
          updated_at: string
        }
        Insert: {
          cover_letter_json: string
          created_at?: string
          id?: number
          job_id: number
          locked?: boolean
          template_name?: string
          updated_at?: string
        }
        Update: {
          cover_letter_json?: string
          created_at?: string
          id?: number
          job_id?: number
          locked?: boolean
          template_name?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "cover_letters_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: true
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      education: {
        Row: {
          created_at: string
          degree: string
          grad_date: string
          id: number
          institution: string
          major: string
          updated_at: string
          user_id: number
        }
        Insert: {
          created_at?: string
          degree: string
          grad_date: string
          id?: number
          institution: string
          major: string
          updated_at?: string
          user_id: number
        }
        Update: {
          created_at?: string
          degree?: string
          grad_date?: string
          id?: number
          institution?: string
          major?: string
          updated_at?: string
          user_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "education_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      experience_proposals: {
        Row: {
          achievement_id: number | null
          created_at: string
          experience_id: number
          id: number
          original_proposed_content: Json
          proposal_type: Database["public"]["Enums"]["proposal_type"]
          proposed_content: Json
          session_id: number
          status: Database["public"]["Enums"]["proposal_status"]
          updated_at: string
        }
        Insert: {
          achievement_id?: number | null
          created_at?: string
          experience_id: number
          id?: number
          original_proposed_content: Json
          proposal_type: Database["public"]["Enums"]["proposal_type"]
          proposed_content: Json
          session_id: number
          status: Database["public"]["Enums"]["proposal_status"]
          updated_at?: string
        }
        Update: {
          achievement_id?: number | null
          created_at?: string
          experience_id?: number
          id?: number
          original_proposed_content?: Json
          proposal_type?: Database["public"]["Enums"]["proposal_type"]
          proposed_content?: Json
          session_id?: number
          status?: Database["public"]["Enums"]["proposal_status"]
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "experience_proposals_achievement_id_fkey"
            columns: ["achievement_id"]
            isOneToOne: false
            referencedRelation: "achievements"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "experience_proposals_experience_id_fkey"
            columns: ["experience_id"]
            isOneToOne: false
            referencedRelation: "experiences"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "experience_proposals_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "job_intake_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      experiences: {
        Row: {
          company_name: string
          company_overview: string | null
          created_at: string
          end_date: string | null
          id: number
          job_title: string
          location: string | null
          role_overview: string | null
          skills: Json
          start_date: string
          updated_at: string
          user_id: number
        }
        Insert: {
          company_name: string
          company_overview?: string | null
          created_at?: string
          end_date?: string | null
          id?: number
          job_title: string
          location?: string | null
          role_overview?: string | null
          skills?: Json
          start_date: string
          updated_at?: string
          user_id: number
        }
        Update: {
          company_name?: string
          company_overview?: string | null
          created_at?: string
          end_date?: string | null
          id?: number
          job_title?: string
          location?: string | null
          role_overview?: string | null
          skills?: Json
          start_date?: string
          updated_at?: string
          user_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "experiences_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      job_intake_chat_messages: {
        Row: {
          created_at: string
          id: number
          messages: Json
          session_id: number
          step: number
        }
        Insert: {
          created_at?: string
          id?: number
          messages: Json
          session_id: number
          step: number
        }
        Update: {
          created_at?: string
          id?: number
          messages?: Json
          session_id?: number
          step?: number
        }
        Relationships: [
          {
            foreignKeyName: "job_intake_chat_messages_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "job_intake_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      job_intake_sessions: {
        Row: {
          completed_at: string | null
          created_at: string
          current_step: number
          gap_analysis: string | null
          id: number
          job_id: number
          resume_chat_thread_id: string | null
          stakeholder_analysis: string | null
          step1_completed: boolean
          step2_completed: boolean
          step3_completed: boolean
          updated_at: string
        }
        Insert: {
          completed_at?: string | null
          created_at?: string
          current_step: number
          gap_analysis?: string | null
          id?: number
          job_id: number
          resume_chat_thread_id?: string | null
          stakeholder_analysis?: string | null
          step1_completed?: boolean
          step2_completed?: boolean
          step3_completed?: boolean
          updated_at?: string
        }
        Update: {
          completed_at?: string | null
          created_at?: string
          current_step?: number
          gap_analysis?: string | null
          id?: number
          job_id?: number
          resume_chat_thread_id?: string | null
          stakeholder_analysis?: string | null
          step1_completed?: boolean
          step2_completed?: boolean
          step3_completed?: boolean
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "job_intake_sessions_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: true
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      jobs: {
        Row: {
          applied_at: string | null
          company_name: string | null
          created_at: string
          has_cover_letter: boolean
          has_resume: boolean
          id: number
          is_favorite: boolean
          job_description: string
          job_title: string | null
          resume_chat_thread_id: string | null
          status: Database["public"]["Enums"]["job_status"]
          updated_at: string
          user_id: number
        }
        Insert: {
          applied_at?: string | null
          company_name?: string | null
          created_at?: string
          has_cover_letter?: boolean
          has_resume?: boolean
          id?: number
          is_favorite?: boolean
          job_description: string
          job_title?: string | null
          resume_chat_thread_id?: string | null
          status?: Database["public"]["Enums"]["job_status"]
          updated_at?: string
          user_id: number
        }
        Update: {
          applied_at?: string | null
          company_name?: string | null
          created_at?: string
          has_cover_letter?: boolean
          has_resume?: boolean
          id?: number
          is_favorite?: boolean
          job_description?: string
          job_title?: string | null
          resume_chat_thread_id?: string | null
          status?: Database["public"]["Enums"]["job_status"]
          updated_at?: string
          user_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "jobs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      messages: {
        Row: {
          body: string
          channel: Database["public"]["Enums"]["message_channel"]
          created_at: string
          id: number
          job_id: number
          sent_at: string | null
          updated_at: string
        }
        Insert: {
          body: string
          channel: Database["public"]["Enums"]["message_channel"]
          created_at?: string
          id?: number
          job_id: number
          sent_at?: string | null
          updated_at?: string
        }
        Update: {
          body?: string
          channel?: Database["public"]["Enums"]["message_channel"]
          created_at?: string
          id?: number
          job_id?: number
          sent_at?: string | null
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "messages_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: false
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      notes: {
        Row: {
          content: string
          created_at: string
          id: number
          job_id: number
          updated_at: string
        }
        Insert: {
          content: string
          created_at?: string
          id?: number
          job_id: number
          updated_at?: string
        }
        Update: {
          content?: string
          created_at?: string
          id?: number
          job_id?: number
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "notes_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: false
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      responses: {
        Row: {
          created_at: string
          id: number
          ignore: boolean
          job_id: number | null
          locked: boolean
          prompt: string
          response: string
          source: Database["public"]["Enums"]["response_source"]
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: number
          ignore?: boolean
          job_id?: number | null
          locked?: boolean
          prompt: string
          response: string
          source: Database["public"]["Enums"]["response_source"]
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: number
          ignore?: boolean
          job_id?: number | null
          locked?: boolean
          prompt?: string
          response?: string
          source?: Database["public"]["Enums"]["response_source"]
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "responses_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: false
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      resume_versions: {
        Row: {
          created_at: string
          created_by_user_id: number
          event_type: Database["public"]["Enums"]["resume_version_event"]
          id: number
          job_id: number
          parent_version_id: number | null
          resume_json: string
          template_name: string
          version_index: number
        }
        Insert: {
          created_at?: string
          created_by_user_id: number
          event_type: Database["public"]["Enums"]["resume_version_event"]
          id?: number
          job_id: number
          parent_version_id?: number | null
          resume_json: string
          template_name: string
          version_index: number
        }
        Update: {
          created_at?: string
          created_by_user_id?: number
          event_type?: Database["public"]["Enums"]["resume_version_event"]
          id?: number
          job_id?: number
          parent_version_id?: number | null
          resume_json?: string
          template_name?: string
          version_index?: number
        }
        Relationships: [
          {
            foreignKeyName: "resume_versions_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: false
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      resumes: {
        Row: {
          created_at: string
          id: number
          job_id: number
          locked: boolean
          pdf_filename: string | null
          resume_json: string
          template_name: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: number
          job_id: number
          locked?: boolean
          pdf_filename?: string | null
          resume_json: string
          template_name: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: number
          job_id?: number
          locked?: boolean
          pdf_filename?: string | null
          resume_json?: string
          template_name?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "resumes_job_id_fkey"
            columns: ["job_id"]
            isOneToOne: true
            referencedRelation: "jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      templates: {
        Row: {
          created_at: string
          description: string | null
          html_content: string
          id: number
          is_default: boolean
          metadata: Json
          name: string
          preview_image_url: string | null
          type: Database["public"]["Enums"]["template_type"]
          updated_at: string
        }
        Insert: {
          created_at?: string
          description?: string | null
          html_content: string
          id?: number
          is_default?: boolean
          metadata?: Json
          name: string
          preview_image_url?: string | null
          type: Database["public"]["Enums"]["template_type"]
          updated_at?: string
        }
        Update: {
          created_at?: string
          description?: string | null
          html_content?: string
          id?: number
          is_default?: boolean
          metadata?: Json
          name?: string
          preview_image_url?: string | null
          type?: Database["public"]["Enums"]["template_type"]
          updated_at?: string
        }
        Relationships: []
      }
      users: {
        Row: {
          address: string | null
          city: string | null
          created_at: string
          email: string | null
          first_name: string
          github_url: string | null
          id: number
          last_name: string
          linkedin_url: string | null
          phone_number: string | null
          state: string | null
          updated_at: string
          website_url: string | null
          zip_code: string | null
        }
        Insert: {
          address?: string | null
          city?: string | null
          created_at?: string
          email?: string | null
          first_name: string
          github_url?: string | null
          id?: number
          last_name: string
          linkedin_url?: string | null
          phone_number?: string | null
          state?: string | null
          updated_at?: string
          website_url?: string | null
          zip_code?: string | null
        }
        Update: {
          address?: string | null
          city?: string | null
          created_at?: string
          email?: string | null
          first_name?: string
          github_url?: string | null
          id?: number
          last_name?: string
          linkedin_url?: string | null
          phone_number?: string | null
          state?: string | null
          updated_at?: string
          website_url?: string | null
          zip_code?: string | null
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      job_status:
        | "Saved"
        | "Applied"
        | "Interviewing"
        | "Not Selected"
        | "No Offer"
        | "Hired"
      message_channel: "email" | "linkedin"
      proposal_status: "pending" | "accepted" | "rejected"
      proposal_type:
        | "achievement_add"
        | "achievement_update"
        | "achievement_delete"
        | "skill_add"
        | "skill_delete"
        | "role_overview_update"
        | "company_overview_update"
      response_source: "manual" | "application"
      resume_version_event: "generate" | "save" | "reset"
      template_type: "resume" | "cover_letter"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      job_status: [
        "Saved",
        "Applied",
        "Interviewing",
        "Not Selected",
        "No Offer",
        "Hired",
      ],
      message_channel: ["email", "linkedin"],
      proposal_status: ["pending", "accepted", "rejected"],
      proposal_type: [
        "achievement_add",
        "achievement_update",
        "achievement_delete",
        "skill_add",
        "skill_delete",
        "role_overview_update",
        "company_overview_update",
      ],
      response_source: ["manual", "application"],
      resume_version_event: ["generate", "save", "reset"],
      template_type: ["resume", "cover_letter"],
    },
  },
} as const

