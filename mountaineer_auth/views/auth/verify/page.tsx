import React from "react";
import { useServer } from "./_server/useServer";
import { VerificationType } from "./_server/models";
import { LinkComponent, ErrorComponent } from "../components";
import ForgotPassword from "./forgot_password";
import InitialVerification from "./initial_verification";

const VerifyPage = () => {
  const serverState = useServer();

  let payload: React.ReactNode | null = null;
  let title = "Verify Email";

  if (serverState.expired) {
    payload = (
      <ErrorComponent>
        The verification link has expired. Please request a new one by going to
        "Forget Password".
      </ErrorComponent>
    );
  } else if (serverState.not_found) {
    payload = (
      <ErrorComponent>
        The verification link is invalid. Please request a new one by going to
        "Forget Password".
      </ErrorComponent>
    );
  } else if (serverState.is_used) {
    payload = (
      <ErrorComponent>
        The verification link has already been used. Please request a new one by
        going to "Forget Password".
      </ErrorComponent>
    );
  } else if (serverState.success) {
    if (serverState.verification_type == VerificationType.INITIAL) {
      payload = <InitialVerification />;
    } else if (
      serverState.verification_type == VerificationType.FORGOT_PASSWORD
    ) {
      title = "Reset Password";
      payload = <ForgotPassword serverState={serverState} />;
    } else {
      throw new Error("Invalid verification type");
    }
  } else {
    throw new Error("Invalid server state");
  }

  return (
    <div className="mx-auto max-w-md px-4">
      <h2 className="mt-6 text-center text-3xl font-bold tracking-tight">
        {title}
      </h2>
      <div className="mt-2 text-center text-sm text-gray-600">
        To login, click{" "}
        <LinkComponent href={serverState.linkGenerator.loginController({})}>
          here.
        </LinkComponent>
      </div>
      <div className="mt-8">{payload}</div>
    </div>
  );
};

export default VerifyPage;
