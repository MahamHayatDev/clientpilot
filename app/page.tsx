"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import Papa from "papaparse";

import {
  bulkAdd,
  listCompanies,
  runBatch,
  runPipeline,
  type Company,
} from "./lib/api";

import { StatusBadge } from "./lib/ui";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [batchBusy, setBatchBusy] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const refreshCompanies = useCallback(async () => {
    try {
      const data = await listCompanies();
      setCompanies(data);
      setError("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load companies."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshCompanies();
  }, [refreshCompanies]);

  async function uploadCsv(file: File) {
    setUploadBusy(true);
    setError("");
    setMessage("");

    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      transformHeader: (header) => header.trim().toLowerCase(),

      complete: async (csvResult) => {
        try {
          if (csvResult.errors.length > 0) {
            throw new Error(
              `CSV parsing issue: ${csvResult.errors[0].message}`
            );
          }

          const rows = csvResult.data
            .map((row) => ({
              name: String(row.name ?? "").trim(),
              website: String(row.website ?? "").trim(),
            }))
            .filter((row) => row.name && row.website);

          if (rows.length === 0) {
            throw new Error(
              "No valid rows found. Your CSV needs name and website columns."
            );
          }

          if (rows.length > 200) {
            throw new Error(
              "Please upload no more than 200 companies at a time."
            );
          }

          const uploadResult = await bulkAdd(rows);

          setMessage(
            `Upload complete: ${uploadResult.added} added and ${uploadResult.skipped} skipped as duplicates or invalid rows.`
          );

          await refreshCompanies();
        } catch (err) {
          setError(
            err instanceof Error ? err.message : "CSV upload failed."
          );
        } finally {
          setUploadBusy(false);

          if (fileRef.current) {
            fileRef.current.value = "";
          }
        }
      },

      error: (err) => {
        setError(err.message || "Could not read the CSV file.");
        setUploadBusy(false);

        if (fileRef.current) {
          fileRef.current.value = "";
        }
      },
    });
  }

  async function processCompany(company: Company) {
    setBusyId(company.id);
    setError("");
    setMessage("");

    try {
      const finished = [
        "drafted",
        "approved",
        "rejected",
        "skipped",
      ].includes(company.status);

      const result = await runPipeline(company.id, finished);

      setMessage(
        `${company.name}: ${result.final_status ?? "processed"}` +
          (result.score != null ? ` · Fit score: ${result.score}` : "") +
          (result.error ? ` · ${result.error}` : "")
      );

      await refreshCompanies();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Could not process ${company.name}.`
      );
    } finally {
      setBusyId(null);
    }
  }

  async function processBatch() {
    setBatchBusy(true);
    setError("");
    setMessage("");

    try {
      const result = await runBatch(3);

      setMessage(
        `Batch processing finished. ${JSON.stringify(result)}`
      );

      await refreshCompanies();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Batch processing failed."
      );
    } finally {
      setBatchBusy(false);
    }
  }

  const draftedCount = companies.filter(
    (company) => company.status === "drafted"
  ).length;

  // Include failed companies so they can be retried.
  const newCount = companies.filter(
    (company) => ["new", "failed"].includes(company.status)
  ).length;

  const averageScore = (() => {
    const scores = companies
      .map((company) => company.fit_score)
      .filter((score): score is number => score !== null);

    return scores.length
      ? Math.round(
          (scores.reduce((sum, score) => sum + score, 0) /
            scores.length) *
            10
        ) / 10
      : null;
  })();

  return (
    <div className="space-y-8">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-700">
            Outreach workspace
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Companies
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
            Research companies, identify opportunities, score their fit,
            and prepare outreach drafts for your review.
          </p>
        </div>

        <button
          onClick={processBatch}
          disabled={batchBusy || loading || newCount === 0}
          className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {batchBusy ? "Processing batch..." : "Process next 3 companies"}
        </button>
      </section>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
        >
          {error}
        </div>
      )}

      {message && (
        <div
          role="status"
          className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
        >
          {message}
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Total companies" value={companies.length} />
        <MetricCard label="Ready to process" value={newCount} />
        <MetricCard label="Drafts created" value={draftedCount} />
        <MetricCard
          label="Average fit score"
          value={averageScore === null ? "—" : averageScore}
        />
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-bold text-slate-950">
              Import companies
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Upload a CSV with the columns{" "}
              <code className="rounded bg-slate-100 px-1.5 py-0.5">
                name
              </code>{" "}
              and{" "}
              <code className="rounded bg-slate-100 px-1.5 py-0.5">
                website
              </code>
              .
            </p>
          </div>

          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploadBusy}
            className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
          >
            {uploadBusy ? "Uploading..." : "Upload CSV"}
          </button>

          <input
            ref={fileRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];

              if (file) {
                void uploadCsv(file);
              }
            }}
          />
        </div>

        <div className="mt-5 rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            CSV example
          </p>

          <pre className="mt-2 overflow-x-auto text-xs leading-6 text-slate-700">
{`name,website
Example Fintech,https://example.com
Example SaaS,https://saas.example.com`}
          </pre>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-200 px-5 py-5 sm:flex-row sm:items-center sm:px-6">
          <div>
            <h2 className="text-lg font-bold text-slate-950">
              Company pipeline
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Select a company to inspect its research and draft.
            </p>
          </div>

          <button
            onClick={() => void refreshCompanies()}
            disabled={loading}
            className="self-start rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 sm:self-auto"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="p-10 text-center text-sm text-slate-500">
            Loading companies...
          </div>
        ) : companies.length === 0 ? (
          <div className="p-10 text-center">
            <p className="font-semibold text-slate-800">
              No companies yet
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Upload a CSV to get started.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-4 font-semibold">Company</th>
                  <th className="px-6 py-4 font-semibold">Fit score</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 text-right font-semibold">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {companies.map((company) => (
                  <tr
                    key={company.id}
                    className="hover:bg-slate-50/70"
                  >
                    <td className="px-6 py-4">
                      <Link
                        href={`/companies/${company.id}`}
                        className="font-semibold text-slate-900 hover:text-blue-700"
                      >
                        {company.name}
                      </Link>

                      <p className="mt-1 max-w-sm truncate text-xs text-slate-500">
                        {company.website || "No website"}
                      </p>
                    </td>

                    <td className="px-6 py-4">
                      {company.fit_score === null ? (
                        <span className="text-slate-400">—</span>
                      ) : (
                        <span className="font-semibold text-slate-800">
                          {company.fit_score}/100
                        </span>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      <StatusBadge status={company.status} />
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-3">
                        <Link
                          href={`/companies/${company.id}`}
                          className="font-medium text-blue-700 hover:text-blue-900"
                        >
                          Details
                        </Link>

                        <button
                          onClick={() => void processCompany(company)}
                          disabled={
                            busyId !== null ||
                            batchBusy ||
                            uploadBusy
                          }
                          className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {busyId === company.id
                            ? "Processing..."
                            : [
                                  "drafted",
                                  "approved",
                                  "rejected",
                                  "skipped",
                                ].includes(company.status)
                              ? "Re-run"
                              : "Run pipeline"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-xs leading-5 text-slate-500">
        AI-generated outreach remains a draft. Review the research and
        wording before using any message. ClientPilot does not send emails
        automatically.
      </p>
    </div>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>

      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
        {value}
      </p>
    </div>
  );
}
