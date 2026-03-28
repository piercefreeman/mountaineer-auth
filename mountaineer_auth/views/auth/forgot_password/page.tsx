import { useState } from "react";
import {
	AuthLayout,
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
		<AuthLayout
			title="Reset your password"
			subtitle={
				<>
					Remember your password?{" "}
					<LinkComponent href={serverState.linkGenerator.loginController({})}>
						Sign in
					</LinkComponent>
				</>
			}
		>
			<form className="grid grid-cols-1 gap-6">
				{forgotPasswordError && (
					<ErrorComponent>
						<span>{forgotPasswordError}</span>
					</ErrorComponent>
				)}
				{serverState.success && (
					<SuccessComponent>
						Check your email for a link to reset your password.
					</SuccessComponent>
				)}
				<div>
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
					<p className="mt-2 text-xs/5 text-zinc-500">
						We&apos;ll send you a link to reset your password.
					</p>
				</div>
				<ButtonComponent
					type="submit"
					disabled={isLoadingSubmit}
					onClick={async (e) => {
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
					Send reset link
				</ButtonComponent>
			</form>
		</AuthLayout>
	);
};

export default ForgotPasswordPage;
