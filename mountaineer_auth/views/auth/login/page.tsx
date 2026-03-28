import { useState } from "react";
import {
	AuthLayout,
	ButtonComponent,
	Divider,
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
		<AuthLayout
			title="Sign in to your account"
			subtitle={
				serverState.include_signup_link ? (
					<>
						Don&apos;t have an account?{" "}
						<LinkComponent
							href={serverState.linkGenerator.signupController({})}
						>
							Create one
						</LinkComponent>
					</>
				) : undefined
			}
		>
			<form className="grid grid-cols-1 gap-6">
				{loginError && (
					<ErrorComponent>
						<span>{loginError}</span>
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
					autoComplete="current-password"
					onChange={(e) => setPassword(e.target.value)}
					placeholder="Enter your password"
					value={password}
				/>
				<ButtonComponent
					type="submit"
					disabled={isLoadingSubmit}
					onClick={async (e) => {
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
					Sign in
				</ButtonComponent>
			</form>
			<div className="mt-6">
				<Divider />
			</div>
			<p className="mt-6 text-center text-sm/6 text-zinc-500">
				<LinkComponent
					href={serverState.linkGenerator.forgotPasswordController({})}
				>
					Forgot your password?
				</LinkComponent>
			</p>
		</AuthLayout>
	);
};

export default LoginPage;
