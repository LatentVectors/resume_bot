import { NextRequest, NextResponse } from "next/server";
import { runJobDetailsExtraction } from "@/lib/langgraph-server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { job_description } = body;

    if (!job_description) {
      return NextResponse.json(
        { error: "job_description is required" },
        { status: 400 }
      );
    }

    const result = await runJobDetailsExtraction({
      job_description,
    });

    return NextResponse.json({
      title: result.title,
      company: result.company,
      confidence: null, // LangGraph doesn't return confidence
    });
  } catch (error) {
    console.error("Job details extraction failed:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

