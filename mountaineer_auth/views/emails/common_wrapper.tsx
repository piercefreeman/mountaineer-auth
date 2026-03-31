import {
	Body,
	Container,
	Font,
	Head,
	Hr,
	Html,
	Img,
	Link,
	Section,
	Text,
} from "@react-email/components";
import { Tailwind } from "@react-email/tailwind";
import type React from "react";

interface CommonConfig {
	header_image: string | null;
	unsubscribe_url: string;
	project_name: string;
	project_address: string;
}

const CommonWrapper = ({
	config,
	children,
	title,
}: {
	config: CommonConfig;
	children: React.ReactNode;
	title: string;
}) => {
	return (
		<Tailwind>
			<Html lang="en">
				<Head>
					<Font
						fontFamily="system-ui"
						fallbackFontFamily="Verdana"
						fontWeight={400}
						fontStyle="normal"
					/>
				</Head>
				<Body className="mx-auto my-0 bg-white font-sans">
					<Container className="mx-auto w-[520px] max-w-[520px] px-6 py-10">
						{/* Header */}
						<Section className="text-center">
							{config.header_image ? (
								<Img
									src={config.header_image}
									alt={config.project_name}
									width="36"
									height="36"
									className="mx-auto"
								/>
							) : (
								<Text className="m-0 text-base font-semibold tracking-tight text-zinc-950">
									{config.project_name}
								</Text>
							)}
						</Section>

						{/* Divider */}
						<Hr className="mx-0 my-6 border-zinc-950/10" />

						{/* Content */}
						<Section>
							<Text className="m-0 text-xl font-semibold tracking-tight text-zinc-950">
								{title}
							</Text>
							<Section className="mt-4">{children}</Section>
						</Section>

						{/* Footer */}
						<Hr className="mx-0 mb-6 mt-10 border-zinc-950/10" />
						<Section>
							<Text className="m-0 text-xs leading-5 text-zinc-400">
								Sent by {config.project_name}, {config.project_address}.
							</Text>
							<Text className="m-0 mt-1 text-xs leading-5 text-zinc-400">
								<Link
									href={config.unsubscribe_url}
									className="text-zinc-400 underline decoration-zinc-400/50 underline-offset-2 transition-colors"
								>
									Unsubscribe
								</Link>
							</Text>
						</Section>
					</Container>
				</Body>
			</Html>
		</Tailwind>
	);
};

export default CommonWrapper;
