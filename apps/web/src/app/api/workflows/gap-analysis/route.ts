import { NextRequest, NextResponse } from "next/server";
import { runGapAnalysis } from "@/lib/langgraph-server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { job_description, work_experience } = body;

    if (!job_description || !work_experience) {
      return NextResponse.json(
        { error: "job_description and work_experience are required" },
        { status: 400 }
      );
    }

    const analysis = await runGapAnalysis({
      job_description,
      work_experience,
    });

    return NextResponse.json({ analysis });
  } catch (error) {
    console.error("Gap analysis failed:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

