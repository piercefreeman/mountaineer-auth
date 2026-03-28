import type React from "react";
import { AuthLayout, ErrorComponent, LinkComponent } from "../components";
import { VerificationType } from "./_server/models";
import { useServer } from "./_server/useServer";
import ForgotPassword from "./forgot_password";
import InitialVerification from "./initial_verification";

const VerifyPage = () => {
	const serverState = useServer();

	let payload: React.ReactNode | null = null;
	let title = "Verify your email";

	if (serverState.expired) {
		payload = (
			<ErrorComponent>
				This verification link has expired. Please request a new one from the
				forgot password page.
			</ErrorComponent>
		);
	} else if (serverState.not_found) {
		payload = (
			<ErrorComponent>
				This verification link is invalid. Please request a new one from the
				forgot password page.
			</ErrorComponent>
		);
	} else if (serverState.is_used) {
		payload = (
			<ErrorComponent>
				This verification link has already been used. Please request a new one
				from the forgot password page.
			</ErrorComponent>
		);
	} else if (serverState.success) {
		if (serverState.verification_type === VerificationType.INITIAL) {
			payload = <InitialVerification />;
		} else if (
			serverState.verification_type === VerificationType.FORGOT_PASSWORD
		) {
			title = "Set a new password";
			payload = <ForgotPassword serverState={serverState} />;
		} else {
			throw new Error("Invalid verification type");
		}
	} else {
		throw new Error("Invalid server state");
	}

	return (
		<AuthLayout
			title={title}
			subtitle={
				<>
					Back to{" "}
					<LinkComponent href={serverState.linkGenerator.loginController({})}>
						sign in
					</LinkComponent>
				</>
			}
		>
			{payload}
		</AuthLayout>
	);
};

export default VerifyPage;
