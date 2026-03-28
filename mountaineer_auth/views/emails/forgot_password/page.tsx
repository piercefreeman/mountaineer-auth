import { Button } from "@react-email/components";
import CommonWrapper from "../common_wrapper";
import { useServer } from "./_server/useServer";

const Page = () => {
	const serverState = useServer();

	// Separating the host from the verification code lets us
	// use dynamic client specified url endpoints
	const relativeVerification = serverState.linkGenerator
		.verifyController({
			verification_code: serverState.verification_code,
		})
		.replace(/^\/+/, "");
	const verificationUrl = `${serverState.verification_host}/${relativeVerification}`;

	return (
		<CommonWrapper title="Reset Password" config={serverState.common_config}>
			<div>
				{serverState.user_name && <div>Hi {serverState.user_name}!</div>}
				<div className="mt-4">
					We received a password reset request for{" "}
					{serverState.common_config.project_name}. If this wasn't you, you can
					safely ignore this email. If it was you, this link expires in 15
					minutes.
				</div>
				<div className="mt-4">
					<Button
						className="box-border w-full rounded-[8px] bg-blue-500 px-[12px] py-[12px] text-center font-semibold text-white"
						href={verificationUrl}
					>
						Reset Email
					</Button>
				</div>
			</div>
		</CommonWrapper>
	);
};

export default Page;
