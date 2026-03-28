import React from "react";
import { useServer } from "./_server/useServer";

const Home = () => {
  const serverState = useServer();
  const detailHref = serverState.detail_id
    ? serverState.linkGenerator.detailController({
        detail_id: serverState.detail_id,
      })
    : undefined;

  return (
    <div className="min-h-screen bg-stone-50 px-6 py-16 text-zinc-950">
      <div className="mx-auto max-w-5xl">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.4fr)_minmax(20rem,1fr)]">
          <section className="rounded-[2rem] border border-zinc-950/10 bg-white p-8 shadow-sm sm:p-10">
            <p className="text-xs/5 font-semibold uppercase tracking-[0.24em] text-zinc-500">
              mountaineer-auth example
            </p>
            <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-zinc-950 sm:text-5xl">
              A minimal Mountaineer app with a real auth guard.
            </h1>
            <p className="mt-5 max-w-2xl text-base/7 text-zinc-600">
              This proof of concept uses a database-backed user model, the
              packaged auth controllers, and a protected detail page that only
              renders for signed-in users.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <a
                className="inline-flex items-center justify-center rounded-full bg-zinc-950 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
                href={detailHref ?? "#"}
              >
                Open protected detail
              </a>
              {!serverState.is_authenticated ? (
                <a
                  className="inline-flex items-center justify-center rounded-full border border-zinc-950/10 bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition-colors hover:border-zinc-950/30"
                  href={serverState.linkGenerator.signupController({})}
                >
                  Create an account
                </a>
              ) : (
                <a
                  className="inline-flex items-center justify-center rounded-full border border-zinc-950/10 bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition-colors hover:border-zinc-950/30"
                  href={serverState.linkGenerator.logoutController({})}
                >
                  Sign out
                </a>
              )}
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-zinc-950/10 bg-zinc-50 p-5">
                <p className="text-xs/5 font-semibold uppercase tracking-[0.2em] text-zinc-500">
                  1
                </p>
                <p className="mt-2 text-sm/6 text-zinc-700">
                  Visit a server-protected route.
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-950/10 bg-zinc-50 p-5">
                <p className="text-xs/5 font-semibold uppercase tracking-[0.2em] text-zinc-500">
                  2
                </p>
                <p className="mt-2 text-sm/6 text-zinc-700">
                  Get redirected through the packaged login flow.
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-950/10 bg-zinc-50 p-5">
                <p className="text-xs/5 font-semibold uppercase tracking-[0.2em] text-zinc-500">
                  3
                </p>
                <p className="mt-2 text-sm/6 text-zinc-700">
                  Land back on the authorized detail page with a valid session.
                </p>
              </div>
            </div>
          </section>

          <aside className="rounded-[2rem] border border-zinc-950/10 bg-zinc-950 p-8 text-white shadow-sm">
            <p className="text-xs/5 font-semibold uppercase tracking-[0.24em] text-zinc-400">
              Session state
            </p>
            <div className="mt-6 rounded-2xl bg-white/5 p-5">
              <p className="text-sm font-medium text-zinc-300">Current user</p>
              <p className="mt-2 text-lg font-semibold text-white">
                {serverState.user_email ?? "Anonymous visitor"}
              </p>
              <p className="mt-3 text-sm/6 text-zinc-300">
                {serverState.is_authenticated
                  ? "Your session cookie is active. Open the protected record to inspect the authenticated user payload."
                  : "Sign up or sign in, then open the protected record to inspect the authenticated user payload."}
              </p>
            </div>

            <div className="mt-6 rounded-2xl border border-white/10 p-5">
              <p className="text-sm font-medium text-zinc-300">
                Seeded detail record
              </p>
              <p className="mt-3 text-sm/6 text-zinc-200">
                {serverState.detail_description ??
                  "The app will create a default protected record on startup."}
              </p>
            </div>

            {!serverState.is_authenticated && (
              <div className="mt-6 flex flex-col gap-3">
                <a
                  className="inline-flex items-center justify-center rounded-full bg-white px-4 py-2.5 text-sm font-semibold text-zinc-950 transition-colors hover:bg-zinc-200"
                  href={serverState.linkGenerator.loginController({})}
                >
                  Sign in
                </a>
                <a
                  className="inline-flex items-center justify-center rounded-full border border-white/15 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:border-white/30"
                  href={serverState.linkGenerator.signupController({})}
                >
                  Sign up
                </a>
              </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Home;
