import React, { useState } from "react";
import {
  ButtonComponent,
  ErrorComponent,
  InputComponent,
  LinkComponent,
} from "../components";
import { useRecaptcha } from "../recaptcha";
import { RequestValidationError, SignupInvalid } from "./_server/actions";
import { useServer } from "./_server/useServer";

const SignupPage = () => {
  const serverState = useServer();

  const [isLoadingSubmit, setIsLoadingSubmit] = useState(false);
  const [signupError, setSignupError] = useState<string | undefined>(undefined);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const recapchaKey =
    serverState.recaptcha_enabled && serverState.recaptcha_client_key
      ? useRecaptcha(
          serverState.recaptcha_client_key,
          serverState.recaptcha_action,
        )
      : null;

  return (
    <div className="mx-auto max-w-md px-4">
      <h2 className="mt-6 text-center text-3xl font-bold tracking-tight">
        Create a new account
      </h2>
      <div className="mt-2 text-center text-sm text-gray-600">
        If you already have one, login{" "}
        <LinkComponent href={serverState.linkGenerator.loginController({})}>
          here.
        </LinkComponent>
      </div>
      <form className="mt-8 space-y-4 rounded bg-white p-8 shadow">
        {signupError && (
          <ErrorComponent>
            <span>{signupError}</span>
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
        <InputComponent
          type="password"
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm Password"
          value={confirmPassword}
        />
        <ButtonComponent
          type="submit"
          disabled={isLoadingSubmit}
          onClick={async (e) => {
            // Disable default form submission
            e.preventDefault();

            // Local validation
            if (password !== confirmPassword) {
              setSignupError("Passwords do not match.");
              return;
            }

            setIsLoadingSubmit(true);

            try {
              const signupResponse = await serverState.signup({
                requestBody: {
                  username: email,
                  password: password,
                  recaptcha_key: recapchaKey,
                },
              });
              setSignupError(undefined);
              window.location.href = serverState.post_signup_redirect;
            } catch (e) {
              if (e instanceof SignupInvalid) {
                setSignupError(e.body.invalid_reason);
              } else if (e instanceof RequestValidationError) {
                setSignupError(e.body.errors[0].message);
              } else {
                setSignupError(
                  "Unknown server error occurred. Please try again.",
                );
                throw e;
              }
            } finally {
              setIsLoadingSubmit(false);
            }
          }}
        >
          Register
        </ButtonComponent>
      </form>
      {serverState.recaptcha_enabled && (
        <div className="mt-4 px-4 text-xs text-gray-400">
          User registration is protected by reCAPTCHA. Google's{" "}
          <a
            className="text-gray-500"
            href="https://policies.google.com/privacy"
          >
            Privacy Policy
          </a>{" "}
          and{" "}
          <a className="text-gray-500" href="https://policies.google.com/terms">
            Terms of Service
          </a>{" "}
          apply.
        </div>
      )}
    </div>
  );
};

export default SignupPage;
