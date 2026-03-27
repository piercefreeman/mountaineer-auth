import React, { useState } from "react";
import {
  ButtonComponent,
  ErrorComponent,
  InputComponent,
  SuccessComponent,
} from "../components";
import {
  RequestValidationError,
  ResetPasswordInvalid,
} from "./_server/actions";
import { ServerState } from "./_server/useServer";

const ForgotPassword = ({ serverState }: { serverState: ServerState }) => {
  const [password, setPassword] = useState("");
  const [verifyPassword, setVerifyPassword] = useState("");

  const [isLoadingSubmit, setIsLoadingSubmit] = useState(false);
  const [forgotPasswordError, setForgotPasswordError] = useState<
    string | undefined
  >(undefined);
  const [success, setSuccess] = useState(false);

  return (
    <div className="mt-8 rounded bg-white p-8 shadow">
      <form className="space-y-4">
        {forgotPasswordError && (
          <ErrorComponent>
            <span>{forgotPasswordError}</span>
          </ErrorComponent>
        )}
        {success && (
          <SuccessComponent>
            Your password has been updated. You can now log in.
          </SuccessComponent>
        )}
        <InputComponent
          type="password"
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          value={password}
        />
        <InputComponent
          type="password"
          onChange={(e) => setVerifyPassword(e.target.value)}
          placeholder="Verify Password"
          value={verifyPassword}
        />
        <ButtonComponent
          type="submit"
          disabled={isLoadingSubmit}
          onClick={async (e) => {
            // Disable default form submission
            e.preventDefault();

            setIsLoadingSubmit(true);

            try {
              await serverState.reset_password({
                verification_code: serverState.verification_code,
                requestBody: {
                  password: password,
                  verify_password: verifyPassword,
                },
              });
              setForgotPasswordError(undefined);
              setSuccess(true);
            } catch (e) {
              setSuccess(false);
              if (e instanceof ResetPasswordInvalid) {
                setForgotPasswordError(e.body.invalid_reason);
              } else if (e instanceof RequestValidationError) {
                setForgotPasswordError(e.body.errors[0].message);
              } else {
                setForgotPasswordError(
                  "Unknown server error occurred. Please try again.",
                );
                throw e;
              }
            } finally {
              setIsLoadingSubmit(false);
            }
          }}
        >
          Update Password
        </ButtonComponent>
      </form>
    </div>
  );
};

export default ForgotPassword;
