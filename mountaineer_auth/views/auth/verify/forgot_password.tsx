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
    <form className="grid grid-cols-1 gap-6">
      {forgotPasswordError && (
        <ErrorComponent>
          <span>{forgotPasswordError}</span>
        </ErrorComponent>
      )}
      {success && (
        <SuccessComponent>
          Your password has been updated. You can now sign in.
        </SuccessComponent>
      )}
      <InputComponent
        label="New password"
        type="password"
        autoComplete="new-password"
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Enter a new password"
        value={password}
      />
      <InputComponent
        label="Confirm password"
        type="password"
        autoComplete="new-password"
        onChange={(e) => setVerifyPassword(e.target.value)}
        placeholder="Confirm your new password"
        value={verifyPassword}
      />
      <ButtonComponent
        type="submit"
        disabled={isLoadingSubmit}
        onClick={async (e) => {
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
        Update password
      </ButtonComponent>
    </form>
  );
};

export default ForgotPassword;
