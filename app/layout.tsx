import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClientPilot | AI Outreach Dashboard",
  description:
    "Research companies, score opportunities, and manage AI-generated outreach drafts.",
};

const navigation = [
  { label: "Companies", href: "/" },
  { label: "Approval Queue", href: "/queue" },
  { label: "Analytics", href: "/analytics" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between lg:px-8">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-lg font-bold text-white">
                C
              </div>

              <div>
                <h1 className="text-xl font-bold tracking-tight">
                  ClientPilot
                </h1>
                <p className="text-xs text-slate-500">
                  AI-powered outreach workspace
                </p>
              </div>
            </Link>

            <nav className="flex flex-wrap items-center gap-2">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
          {children}
        </main>

        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-7xl px-5 py-5 text-xs text-slate-500 lg:px-8">
            ClientPilot · Research, qualify, and review before outreach.
          </div>
        </footer>
      </body>
    </html>
  );
}