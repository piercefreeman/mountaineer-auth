import { Button, Text } from "@react-email/components";
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
		<CommonWrapper title="Verify your email" config={serverState.common_config}>
			{serverState.user_name && (
				<Text className="m-0 text-sm leading-6 text-zinc-950">
					Hi {serverState.user_name},
				</Text>
			)}
			<Text className="m-0 mt-2 text-sm leading-6 text-zinc-500">
				Thanks for signing up for {serverState.common_config.project_name}.
				Confirm your email address by clicking the button below. This link
				expires in 24 hours.
			</Text>
			<Button
				className="mt-6 box-border inline-flex rounded-lg bg-zinc-950 px-5 py-2.5 text-center text-sm font-semibold text-white"
				href={verificationUrl}
			>
				Verify email
			</Button>
			<Text className="m-0 mt-6 text-xs leading-5 text-zinc-400">
				If you didn&apos;t create an account, you can safely ignore this email.
			</Text>
		</CommonWrapper>
	);
};

export default Page;
