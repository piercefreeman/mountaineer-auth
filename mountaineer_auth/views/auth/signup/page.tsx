import React, { useState } from "react";
import {
  AuthLayout,
  ButtonComponent,
  ErrorComponent,
  InputComponent,
  LinkComponent,
} from "../components";
import { RequestValidationError, SignupInvalid } from "./_server/actions";
import { useServer } from "./_server/useServer";

const SignupPage = () => {
  const serverState = useServer();

  const [isLoadingSubmit, setIsLoadingSubmit] = useState(false);
  const [signupError, setSignupError] = useState<string | undefined>(undefined);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  return (
    <AuthLayout
      title="Create your account"
      subtitle={
        <>
          Already have an account?{" "}
          <LinkComponent href={serverState.linkGenerator.loginController({})}>
            Sign in
          </LinkComponent>
        </>
      }
    >
      <form className="grid grid-cols-1 gap-6">
        {signupError && (
          <ErrorComponent>
            <span>{signupError}</span>
          </ErrorComponent>
        )}
        <InputComponent
          label="Email"
          type="email"
          autoComplete="email"
          onChange={(e) => {
            setEmail(e.target.value);
          }}
          placeholder="you@example.com"
          value={email}
        />
        <InputComponent
          label="Password"
          type="password"
          autoComplete="new-password"
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Create a password"
          value={password}
        />
        <InputComponent
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm your password"
          value={confirmPassword}
        />
        <ButtonComponent
          type="submit"
          disabled={isLoadingSubmit}
          onClick={async (e) => {
            e.preventDefault();

            if (password !== confirmPassword) {
              setSignupError("Passwords do not match.");
              return;
            }

            setIsLoadingSubmit(true);

            try {
              await serverState.signup({
                requestBody: {
                  username: email,
                  password: password,
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
          Create account
        </ButtonComponent>
      </form>
    </AuthLayout>
  );
};

export default SignupPage;
