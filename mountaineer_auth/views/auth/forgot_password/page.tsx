import React, { useState } from "react";
import {
  ButtonComponent,
  ErrorComponent,
  InputComponent,
  LinkComponent,
  SuccessComponent,
} from "../components";
import { RequestValidationError } from "./_server/actions";
import { useServer } from "./_server/useServer";

const ForgotPasswordPage = () => {
  const serverState = useServer();

  const [isLoadingSubmit, setIsLoadingSubmit] = useState(false);
  const [forgotPasswordError, setForgotPasswordError] = useState<
    string | undefined
  >(undefined);

  const [email, setEmail] = useState("");

  return (
    <div className="mx-auto max-w-md px-4">
      <h2 className="mt-6 text-center text-3xl font-bold tracking-tight">
        Forgot password
      </h2>
      <div className="mt-2 text-center text-sm text-gray-600">
        If you remembed it,{" "}
        <LinkComponent href={serverState.linkGenerator.loginController({})}>
          log back in.
        </LinkComponent>
      </div>
      <div className="mt-8 rounded bg-white p-8 shadow">
        <form className="space-y-4">
          {forgotPasswordError && (
            <ErrorComponent>
              <span>{forgotPasswordError}</span>
            </ErrorComponent>
          )}
          {serverState.success && (
            <SuccessComponent>
              <span>Check your email for a link to reset your password.</span>
            </SuccessComponent>
          )}
          <InputComponent
            type="email"
            onChange={(e) => {
              setEmail(e.target.value);
            }}
            placeholder="Email"
            value={email}
          />
          <ButtonComponent
            type="submit"
            disabled={isLoadingSubmit}
            onClick={async (e) => {
              // Disable default form submission
              e.preventDefault();

              setIsLoadingSubmit(true);

              try {
                await serverState.forgot_password({
                  requestBody: {
                    username: email,
                  },
                });
                setForgotPasswordError(undefined);
                window.location.href =
                  serverState.linkGenerator.forgotPasswordController({
                    success: true,
                  });
              } catch (e) {
                if (e instanceof RequestValidationError) {
                  setForgotPasswordError(e.body.errors[0].message);
                } else {
                  throw e;
                }
              } finally {
                setIsLoadingSubmit(false);
              }
            }}
          >
            Reset password
          </ButtonComponent>
        </form>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
