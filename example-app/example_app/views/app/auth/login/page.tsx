import React, { useState } from "react";
import { LoginInvalid, RequestValidationError } from "./_server/actions";
import { useServer } from "./_server/useServer";

const LoginPage = () => {
  const serverState = useServer();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="min-h-dvh bg-stone-50 px-4 py-12">
      <div className="mx-auto w-full max-w-4xl rounded-[2rem] border border-zinc-950/10 bg-white shadow-sm lg:grid lg:grid-cols-[minmax(18rem,22rem)_minmax(0,1fr)]">
        <aside className="rounded-t-[2rem] bg-zinc-950 p-8 text-white lg:rounded-l-[2rem] lg:rounded-tr-none">
          <p className="text-xs/5 font-semibold uppercase tracking-[0.24em] text-zinc-400">
            mountaineer-auth example
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">
            Sign in to continue.
          </h1>
          <p className="mt-4 text-sm/6 text-zinc-300">
            The protected detail page requires a valid session cookie. Sign in
            with an existing user or create a new account from the signup flow.
          </p>
          <div className="mt-8 rounded-2xl bg-white/5 p-5">
            <p className="text-sm font-medium text-zinc-300">After login</p>
            <p className="mt-2 text-sm/6 text-zinc-200">
              You&apos;ll be redirected to the protected route that triggered the
              auth check, or back to the homepage if you opened login directly.
            </p>
          </div>
        </aside>

        <section className="p-8 sm:p-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-zinc-500">
                Need an account?
              </p>
              <a
                className="mt-1 inline-flex text-sm font-semibold text-zinc-950 underline decoration-zinc-950/30 underline-offset-4 transition-colors hover:decoration-zinc-950"
                href={serverState.linkGenerator.signupController({})}
              >
                Create one here
              </a>
            </div>
            <a
              className="inline-flex items-center justify-center rounded-full border border-zinc-950/10 px-4 py-2 text-sm font-semibold text-zinc-950 transition-colors hover:border-zinc-950/30"
              href={serverState.linkGenerator.homeController({})}
            >
              Back home
            </a>
          </div>

          <form className="mt-10 grid grid-cols-1 gap-5">
            {error && (
              <div
                className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm/6 text-red-900"
                role="alert"
              >
                {error}
              </div>
            )}

            <div>
              <label className="mb-2 block text-sm/6 font-medium text-zinc-950">
                Email
              </label>
              <input
                className="block w-full rounded-2xl border border-zinc-950/10 bg-white px-4 py-3 text-sm/6 text-zinc-950 placeholder:text-zinc-400 transition-colors hover:border-zinc-950/20 focus:border-zinc-950 focus:outline-none focus:ring-2 focus:ring-zinc-950/5"
                type="email"
                autoComplete="email"
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                value={email}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm/6 font-medium text-zinc-950">
                Password
              </label>
              <input
                className="block w-full rounded-2xl border border-zinc-950/10 bg-white px-4 py-3 text-sm/6 text-zinc-950 placeholder:text-zinc-400 transition-colors hover:border-zinc-950/20 focus:border-zinc-950 focus:outline-none focus:ring-2 focus:ring-zinc-950/5"
                type="password"
                autoComplete="current-password"
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                value={password}
              />
            </div>

            <button
              className="mt-2 inline-flex w-full items-center justify-center rounded-full bg-zinc-950 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-default disabled:opacity-50"
              type="submit"
              disabled={isLoading}
              onClick={async (e) => {
                e.preventDefault();
                setIsLoading(true);

                try {
                  await serverState.login({
                    requestBody: {
                      username: email,
                      password: password,
                    },
                  });
                  setError(undefined);
                  window.location.href = serverState.post_login_redirect;
                } catch (error) {
                  if (error instanceof LoginInvalid) {
                    setError(error.body.invalid_reason);
                  } else if (error instanceof RequestValidationError) {
                    setError(error.body.errors[0].message);
                  } else {
                    setError("Unknown server error occurred. Please try again.");
                    throw error;
                  }
                } finally {
                  setIsLoading(false);
                }
              }}
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
};

export default LoginPage;
