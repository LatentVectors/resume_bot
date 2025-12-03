import { NextRequest, NextResponse } from "next/server";
import { runExperienceExtraction } from "@/lib/langgraph-server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { thread_id, work_experience } = body;

    if (!thread_id || !work_experience) {
      return NextResponse.json(
        { error: "thread_id and work_experience are required" },
        { status: 400 }
      );
    }

    const suggestions = await runExperienceExtraction({
      thread_id,
      work_experience,
    });

    return NextResponse.json({ suggestions });
  } catch (error) {
    console.error("Experience extraction failed:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

