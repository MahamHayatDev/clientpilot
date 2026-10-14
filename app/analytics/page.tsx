"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getStats, type DashboardStats } from "../lib/api";
import { StatusBadge } from "../lib/ui";

export default function AnalyticsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadStats = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await getStats();
      setStats(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load analytics."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  const metrics = [
    {
      label: "Total companies",
      value: stats?.total ?? 0,
      description: "Companies in your pipeline",
    },
    {
      label: "Average fit score",
      value:
        stats?.avg_score != null
          ? `${stats.avg_score.toFixed(1)} / 100`
          : "—",
      description: "Average company suitability",
    },
    {
      label: "Awaiting approval",
      value: stats?.waiting ?? 0,
      description: "Drafts waiting for your review",
    },
    {
      label: "Approved drafts",
      value: stats?.approved ?? 0,
      description: "Drafts approved by you",
    },
    {
      label: "Rejected drafts",
      value: stats?.rejected ?? 0,
      description: "Drafts rejected by you",
    },
    {
      label: "Approval rate",
      value:
        stats?.approval_rate != null
          ? `${stats.approval_rate.toFixed(1)}%`
          : "—",
      description: "Approval rate reported by the backend",
    },
  ];

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
            Performance overview
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Analytics
          </h1>

          <p className="mt-2 text-sm text-slate-600">
            Track your company pipeline and outreach approval activity.
          </p>
        </div>

        <div className="flex gap-3">
          <Link
            href="/"
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
          >
            Companies
          </Link>

          <button
            onClick={() => void loadStats()}
            disabled={loading}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-semibold text-red-800">
            Unable to load analytics
          </p>
          <p className="mt-1 text-sm text-red-700">{error}</p>
          <button
            onClick={() => void loadStats()}
            className="mt-3 text-sm font-semibold text-red-800 underline"
          >
            Try again
          </button>
        </div>
      )}

      {loading && !stats ? (
        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
          Loading analytics...
        </div>
      ) : stats ? (
        <>
          <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {metrics.map((metric) => (
              <div
                key={metric.label}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <p className="text-sm font-medium text-slate-500">
                  {metric.label}
                </p>

                <p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
                  {metric.value}
                </p>

                <p className="mt-2 text-xs leading-5 text-slate-500">
                  {metric.description}
                </p>
              </div>
            ))}
          </section>

          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div>
              <h2 className="text-xl font-semibold text-slate-950">
                Pipeline breakdown
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Number of companies currently in each pipeline status.
              </p>
            </div>

            {Object.keys(stats.by_status).length > 0 ? (
              <div className="mt-5 divide-y divide-slate-100">
                {Object.entries(stats.by_status)
                  .sort((a, b) => b[1] - a[1])
                  .map(([status, count]) => {
                    const percentage =
                      stats.total > 0
                        ? Math.min((count / stats.total) * 100, 100)
                        : 0;

                    return (
                      <div
                        key={status}
                        className="flex flex-wrap items-center gap-4 py-4"
                      >
                        <div className="w-32">
                          <StatusBadge status={status} />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-slate-800 transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>

                        <div className="w-12 text-right text-sm font-semibold text-slate-900">
                          {count}
                        </div>

                        <div className="w-14 text-right text-xs text-slate-500">
                          {percentage.toFixed(0)}%
                        </div>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <p className="mt-5 text-sm text-slate-500">
                No pipeline status data is available yet.
              </p>
            )}
          </section>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/queue"
              className="rounded-lg bg-slate-900 px-5 py-3 text-sm font-medium text-white hover:bg-slate-700"
            >
              Review outreach drafts →
            </Link>

            <Link
              href="/"
              className="rounded-lg border border-slate-200 bg-white px-5 py-3 text-sm font-medium text-slate-800 hover:bg-slate-50"
            >
              View companies →
            </Link>
          </div>
        </>
      ) : null}
    </main>
  );
}