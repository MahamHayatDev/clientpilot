"use client";

import { useCallback, useEffect, useState } from "react";

import {
  approveDraft,
  editDraft,
  listDrafts,
  rejectDraft,
  type Draft,
} from "../lib/api";

import { StatusBadge } from "../lib/ui";

type View = "waiting" | "approved" | "rejected";

export default function QueuePage() {
  const [view, setView] = useState<View>("waiting");
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await listDrafts(view);
      setDrafts(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load the approval queue."
      );
    } finally {
      setLoading(false);
    }
  }, [view]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function beginEditing(draft: Draft) {
    setEditingId(draft.id);
    setSubject(draft.subject);
    setBody(draft.body);
    setMessage("");
    setError("");
  }

  async function saveDraft(draft: Draft) {
    setBusyId(draft.id);
    setError("");
    setMessage("");

    try {
      await editDraft(draft.id, subject, body);
      setEditingId(null);
      setMessage(`Changes saved for ${draft.company_name ?? "this company"}.`);
      await refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not save the draft."
      );
    } finally {
      setBusyId(null);
    }
  }

  async function decide(draft: Draft, action: "approve" | "reject") {
    const label = action === "approve" ? "approve" : "reject";

    if (
      !window.confirm(
        `Are you sure you want to ${label} the draft for ${draft.company_name ?? "this company"}?`
      )
    ) {
      return;
    }

    setBusyId(draft.id);
    setError("");
    setMessage("");

    try {
      if (action === "approve") {
        await approveDraft(draft.id);
      } else {
        await rejectDraft(draft.id);
      }

      setEditingId(null);
      setMessage(
        `Draft ${action === "approve" ? "approved" : "rejected"}.`
      );
      await refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Could not ${label} the draft.`
      );
    } finally {
      setBusyId(null);
    }
  }

  async function copyDraft(draft: Draft) {
    try {
      await navigator.clipboard.writeText(
        `Subject: ${draft.subject}\n\n${draft.body}`
      );
      setMessage(`Copied the draft for ${draft.company_name ?? "this company"}.`);
      setError("");
    } catch {
      setError(
        "Could not access the clipboard. Select and copy the draft manually."
      );
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-700">
          Review workspace
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
          Approval Queue
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
          Review every outreach message before using it. Edit the wording,
          approve suitable drafts, or reject messages that are not a good fit.
        </p>
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

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["waiting", "Awaiting review"],
            ["approved", "Approved"],
            ["rejected", "Rejected"],
          ] as [View, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => {
              setView(key);
              setEditingId(null);
              setMessage("");
              setError("");
            }}
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
              view === key
                ? "bg-slate-900 text-white"
                : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">
          Loading drafts...
        </div>
      ) : drafts.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
          <h2 className="font-semibold text-slate-900">
            {view === "waiting"
              ? "No drafts awaiting review"
              : `No ${view} drafts yet`}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            {view === "waiting"
              ? "Run the pipeline for a suitable company to create a draft."
              : "Drafts will appear here when their approval status changes."}
          </p>
        </div>
      ) : (
        <div className="space-y-5">
          {drafts.map((draft) => {
            const isEditing = editingId === draft.id;
            const isBusy = busyId === draft.id;

            return (
              <article
                key={draft.id}
                className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
              >
                <div className="flex flex-col justify-between gap-4 border-b border-slate-100 p-5 sm:flex-row sm:items-start sm:px-6">
                  <div className="min-w-0">
                    <h2 className="text-lg font-bold text-slate-950">
                      {draft.company_name ?? "Unknown company"}
                    </h2>

                    {draft.company_website && (
                      <p className="mt-1 break-all text-sm text-slate-500">
                        {draft.company_website}
                      </p>
                    )}

                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <StatusBadge status={draft.approval_status} />

                      {draft.fit_score != null && (
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                          Fit score: {draft.fit_score}/100
                        </span>
                      )}
                    </div>
                  </div>

                  {draft.score_reasoning && (
                    <div className="max-w-md rounded-xl bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Scoring rationale
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">
                        {draft.score_reasoning}
                      </p>
                    </div>
                  )}
                </div>

                <div className="space-y-5 p-5 sm:p-6">
                  <div>
                    <label
                      htmlFor={`subject-${draft.id}`}
                      className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      Email subject
                    </label>

                    {isEditing ? (
                      <input
                        id={`subject-${draft.id}`}
                        value={subject}
                        onChange={(event) => setSubject(event.target.value)}
                        maxLength={200}
                        className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      />
                    ) : (
                      <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900">
                        {draft.subject}
                      </div>
                    )}
                  </div>

                  <div>
                    <label
                      htmlFor={`body-${draft.id}`}
                      className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      Email body
                    </label>

                    {isEditing ? (
                      <textarea
                        id={`body-${draft.id}`}
                        value={body}
                        onChange={(event) => setBody(event.target.value)}
                        rows={7}
                        maxLength={10000}
                        className="w-full resize-y rounded-xl border border-slate-300 px-4 py-3 text-sm leading-6 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      />
                    ) : (
                      <div className="whitespace-pre-wrap rounded-xl bg-slate-50 px-4 py-4 text-sm leading-7 text-slate-700">
                        {draft.body}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-5">
                    {isEditing ? (
                      <>
                        <button
                          onClick={() => void saveDraft(draft)}
                          disabled={isBusy || !subject.trim() || !body.trim()}
                          className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50"
                        >
                          {isBusy ? "Saving..." : "Save changes"}
                        </button>

                        <button
                          onClick={() => setEditingId(null)}
                          disabled={isBusy}
                          className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        {view === "waiting" && (
                          <>
                            <button
                              onClick={() => beginEditing(draft)}
                              disabled={isBusy || busyId !== null}
                              className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                            >
                              Edit draft
                            </button>

                            <button
                              onClick={() => void decide(draft, "approve")}
                              disabled={isBusy || busyId !== null}
                              className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                            >
                              {isBusy ? "Processing..." : "Approve"}
                            </button>

                            <button
                              onClick={() => void decide(draft, "reject")}
                              disabled={isBusy || busyId !== null}
                              className="rounded-xl border border-rose-200 px-4 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                            >
                              Reject
                            </button>
                          </>
                        )}

                        {view === "approved" && (
                          <button
                            onClick={() => void copyDraft(draft)}
                            className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700"
                          >
                            Copy approved draft
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}