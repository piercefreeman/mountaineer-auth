import React, { useState } from "react";
import { useServer } from "./_server/useServer";

const Page = () => {
  const serverState = useServer();
  const [description, setDescription] = useState(serverState.description);
  const [text, setText] = useState(serverState.description);
  const [isSaving, setIsSaving] = useState(false);

  return (
    <div className="min-h-screen bg-stone-50 px-6 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs/5 font-semibold uppercase tracking-[0.24em] text-zinc-500">
              Protected route
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-950">
              Authenticated detail page
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <a
              className="inline-flex items-center justify-center rounded-full border border-zinc-950/10 bg-white px-4 py-2.5 text-sm font-semibold text-zinc-950 transition-colors hover:border-zinc-950/30"
              href={serverState.linkGenerator.homeController({})}
            >
              Home
            </a>
            <a
              className="inline-flex items-center justify-center rounded-full bg-zinc-950 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
              href={serverState.linkGenerator.logoutController({})}
            >
              Logout
            </a>
          </div>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(18rem,22rem)_minmax(0,1fr)]">
          <section className="rounded-[1.75rem] border border-zinc-950/10 bg-zinc-950 p-6 text-white shadow-sm">
            <p className="text-xs/5 font-semibold uppercase tracking-[0.24em] text-zinc-400">
              Authenticated user
            </p>
            <div className="mt-6 space-y-5">
              <div>
                <p className="text-sm font-medium text-zinc-400">Email</p>
                <p className="mt-1 text-base font-semibold text-white">
                  {serverState.user_email}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-zinc-400">User ID</p>
                <p className="mt-1 break-all text-sm/6 text-zinc-200">
                  {serverState.user_id}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-xs/5 font-semibold uppercase tracking-[0.2em] text-zinc-400">
                    Verified
                  </p>
                  <p className="mt-2 text-base font-semibold text-white">
                    {serverState.is_verified ? "Yes" : "No"}
                  </p>
                </div>
                <div className="rounded-2xl bg-white/5 p-4">
                  <p className="text-xs/5 font-semibold uppercase tracking-[0.2em] text-zinc-400">
                    Admin
                  </p>
                  <p className="mt-2 text-base font-semibold text-white">
                    {serverState.is_admin ? "Yes" : "No"}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-zinc-950/10 bg-white p-6 shadow-sm">
            <div className="rounded-2xl border border-zinc-950/10 bg-stone-50 p-5">
              <p className="text-xs/5 font-semibold uppercase tracking-[0.24em] text-zinc-500">
                Protected record #{serverState.id}
              </p>
              <p className="mt-3 text-base/7 text-zinc-700">{description}</p>
            </div>

            <div className="mt-6">
              <h2 className="text-sm font-semibold text-zinc-950">
                Update the record
              </h2>
              <p className="mt-2 text-sm/6 text-zinc-500">
                This calls a protected sideeffect, so both the initial page load
                and the mutation are behind auth.
              </p>

              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <input
                  className="flex-1 rounded-full border border-zinc-950/10 bg-transparent px-4 py-3 text-sm/6 text-zinc-950 placeholder:text-zinc-400 transition-colors hover:border-zinc-950/20 focus:border-zinc-950 focus:outline-none focus:ring-2 focus:ring-zinc-950/5"
                  type="text"
                  value={text}
                  placeholder="Enter new description..."
                  onChange={(e) => setText(e.target.value)}
                />
                <button
                  className="inline-flex items-center justify-center rounded-full bg-zinc-950 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-default disabled:opacity-40"
                  onClick={async () => {
                    setIsSaving(true);
                    try {
                      await serverState.update_text({
                        detail_id: serverState.id,
                        requestBody: {
                          description: text,
                        },
                      });
                      const trimmedText = text.trim();
                      setDescription(trimmedText);
                      setText(trimmedText);
                    } finally {
                      setIsSaving(false);
                    }
                  }}
                  disabled={!text.trim() || isSaving}
                >
                  {isSaving ? "Saving..." : "Save change"}
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default Page;
