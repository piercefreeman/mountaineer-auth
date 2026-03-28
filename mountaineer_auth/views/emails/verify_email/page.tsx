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
		<CommonWrapper title="Verify Email" config={serverState.common_config}>
			<div>
				{serverState.user_name && <div>Hi {serverState.user_name}!</div>}
				<div className="mt-4">
					You just signed up for {serverState.common_config.project_name}. Use
					this link to confirm your email. This link expires in 24 hours.
				</div>
				<div className="mt-4">
					<a href={verificationUrl}>
						<Button
							className="box-border w-full rounded-[8px] bg-blue-500 px-[12px] py-[12px] text-center font-semibold text-white"
							href={verificationUrl}
						>
							Verify Email
						</Button>
					</a>
				</div>
			</div>
		</CommonWrapper>
	);
};

export default Page;
