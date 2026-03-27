import React, { useState } from "react";
import {
  ButtonComponent,
  ErrorComponent,
  InputComponent,
  LinkComponent,
} from "../components";
import { LoginInvalid, RequestValidationError } from "./_server/actions";
import { useServer } from "./_server/useServer";

const LoginPage = () => {
  const serverState = useServer();

  const [isLoadingSubmit, setIsLoadingSubmit] = useState(false);
  const [loginError, setLoginError] = useState<string | undefined>(undefined);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div className="mx-auto max-w-md px-4">
      <h2 className="mt-6 text-center text-3xl font-bold tracking-tight">
        Sign in to your account
      </h2>

      {serverState.include_signup_link && (
        <div className="mt-2 text-center text-sm text-gray-600">
          If you don't have an account, sign up{" "}
          <LinkComponent href={serverState.linkGenerator.signupController({})}>
            here.
          </LinkComponent>
        </div>
      )}

      <div className="mt-8 rounded bg-white p-8 shadow">
        <form className="space-y-4">
          {loginError && (
            <ErrorComponent>
              <span>{loginError}</span>
            </ErrorComponent>
          )}
          <InputComponent
            type="email"
            onChange={(e) => {
              setEmail(e.target.value);
            }}
            placeholder="Email"
            value={email}
          />
          <InputComponent
            type="password"
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            value={password}
          />
          <ButtonComponent
            type="submit"
            disabled={isLoadingSubmit}
            onClick={async (e) => {
              // Disable default form submission
              e.preventDefault();

              setIsLoadingSubmit(true);

              try {
                await serverState.login({
                  requestBody: {
                    username: email,
                    password: password,
                  },
                });
                setLoginError(undefined);
                window.location.href = serverState.post_login_redirect;
              } catch (e) {
                if (e instanceof LoginInvalid) {
                  setLoginError(e.body.invalid_reason);
                } else if (e instanceof RequestValidationError) {
                  setLoginError(e.body.errors[0].message);
                } else {
                  setLoginError(
                    "Unknown server error occurred. Please try again.",
                  );
                  throw e;
                }
              } finally {
                setIsLoadingSubmit(false);
              }
            }}
          >
            Login
          </ButtonComponent>
        </form>
        <div className="mt-1 text-center text-sm">
          <LinkComponent
            href={serverState.linkGenerator.forgotPasswordController({})}
          >
            Forgot your password?
          </LinkComponent>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
