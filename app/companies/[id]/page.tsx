"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  companyDetail,
  runPipeline,
  type CompanyDetail,
} from "../../lib/api";
import { StatusBadge } from "../../lib/ui";

export default function CompanyDetailPage() {
  const params = useParams();
  const id = String(params.id);

  const [data, setData] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadCompany = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await companyDetail(id);
      setData(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load company details."
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadCompany();
  }, [loadCompany]);

  async function handleRerun() {
    if (!data) return;

    const confirmed = window.confirm(
      `Rerun the research and outreach pipeline for ${data.company.name}?`
    );

    if (!confirmed) return;

    setRunning(true);
    setError("");
    setMessage("");

    try {
      const result = await runPipeline(data.company.id, true);

      setMessage(
        `Pipeline finished. Status: ${
          result.final_status ?? "completed"
        }${result.score != null ? ` · Fit score: ${result.score}` : ""}`
      );

      await loadCompany();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "The pipeline could not be completed."
      );
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <p className="text-sm text-slate-500">
          Loading company details...
        </p>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <Link href="/" className="text-sm text-blue-700 hover:underline">
          ← Back to companies
        </Link>

        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5">
          <h1 className="font-semibold text-red-800">
            Could not load company
          </h1>
          <p className="mt-2 text-sm text-red-700">{error}</p>

          <button
            onClick={() => void loadCompany()}
            className="mt-4 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white"
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const { company, research, score, draft } = data;

  const gaps = Array.isArray(research?.gaps)
    ? research.gaps
    : research?.gaps
      ? [research.gaps]
      : research?.raw?.gaps ?? [];

  const matchedServices = score?.matched_services ?? [];

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/"
          className="text-sm font-medium text-slate-600 hover:text-slate-950"
        >
          ← Back to companies
        </Link>

        <div className="flex gap-3">
          <Link
            href="/queue"
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
          >
            Approval queue
          </Link>

          <button
            onClick={handleRerun}
            disabled={running}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {running ? "Running pipeline..." : "Rerun pipeline"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {message && (
        <div className="mb-5 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          {message}
        </div>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Company profile
            </p>

            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {company.name}
            </h1>

            {company.website ? (
              <a
                href={company.website}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-block text-sm text-blue-700 hover:underline"
              >
                {company.website}
              </a>
            ) : (
              <p className="mt-2 text-sm text-slate-500">
                No website provided
              </p>
            )}
          </div>

          <StatusBadge status={company.status} />
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Fit score</p>
            <p className="mt-1 text-3xl font-bold text-slate-950">
              {company.fit_score ?? score?.fit_score ?? "—"}
              <span className="ml-1 text-base font-normal text-slate-500">
                {company.fit_score != null || score?.fit_score != null
                  ? "/ 100"
                  : ""}
              </span>
            </p>
          </div>

          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Outreach draft</p>
            <p className="mt-1 text-xl font-semibold text-slate-950">
              {draft ? "Available" : "Not created"}
            </p>
            {draft && (
              <div className="mt-2">
                <StatusBadge status={draft.approval_status} />
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-950">
          Company research
        </h2>

        {research ? (
          <div className="mt-4 space-y-5">
            <div>
              <h3 className="text-sm font-semibold text-slate-700">
                Summary
              </h3>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">
                {research.summary ||
                  research.raw?.what_they_do ||
                  "No research summary available yet."}
              </p>
            </div>

            {research.raw?.audience && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700">
                  Target audience
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {research.raw.audience}
                </p>
              </div>
            )}

            {gaps.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700">
                  Potential gaps and opportunities
                </h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
                  {gaps.map((gap, index) => (
                    <li key={`${index}-${gap}`}>{gap}</li>
                  ))}
                </ul>
              </div>
            )}

            {research.raw?.confidence && (
              <p className="text-xs text-slate-500">
                Research confidence: {research.raw.confidence}
              </p>
            )}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            Research has not been generated for this company yet.
          </p>
        )}
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-950">
          Fit assessment
        </h2>

        {score ? (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-700">
                Reasoning
              </h3>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">
                {score.reasoning || "No scoring explanation available."}
              </p>
            </div>

            {matchedServices.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700">
                  Matching services
                </h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {matchedServices.map((service) => (
                    <span
                      key={service}
                      className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700"
                    >
                      {service}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            A fit assessment has not been generated yet.
          </p>
        )}
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-slate-950">
            Outreach draft
          </h2>

          {draft && (
            <Link
              href="/queue"
              className="text-sm font-medium text-blue-700 hover:underline"
            >
              Open approval queue →
            </Link>
          )}
        </div>

        {draft ? (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-700">
                Subject
              </h3>
              <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-800">
                {draft.subject || "(No subject)"}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-700">
                Message
              </h3>
              <p className="mt-2 whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-sm leading-6 text-slate-700">
                {draft.body || "(No message body)"}
              </p>
            </div>

            <p className="text-xs text-slate-500">
              Review and edit this draft in the approval queue before using it.
            </p>
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            No outreach draft is available for this company yet.
          </p>
        )}
      </section>
    </main>
  );
}