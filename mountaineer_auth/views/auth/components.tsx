import {
	type AnchorHTMLAttributes,
	type ButtonHTMLAttributes,
	type InputHTMLAttributes,
	type ReactNode,
	useId,
} from "react";

export const AuthLayout = ({
	title,
	subtitle,
	children,
}: {
	title: string;
	subtitle?: ReactNode;
	children: ReactNode;
}) => {
	return (
		<div className="flex min-h-dvh items-center justify-center px-4 py-12">
			<div className="w-full max-w-sm">
				<div className="text-center">
					<h1 className="text-2xl font-semibold tracking-tight text-zinc-950">
						{title}
					</h1>
					{subtitle && (
						<p className="mt-2 text-sm/6 text-zinc-500">{subtitle}</p>
					)}
				</div>
				<div className="mt-8">{children}</div>
			</div>
		</div>
	);
};

export const InputComponent = (
	props: InputHTMLAttributes<HTMLInputElement> & { label?: string },
) => {
	const { label, ...inputProps } = props;
	const fallbackId = useId();
	const inputId = inputProps.id ?? fallbackId;
	return (
		<div>
			{label && (
				<label
					className="mb-2 block text-sm/6 font-medium text-zinc-950"
					htmlFor={inputId}
				>
					{label}
				</label>
			)}
			<input
				{...inputProps}
				className="block w-full rounded-lg border border-zinc-950/10 bg-white px-3.5 py-2.5 text-sm/6 text-zinc-950 placeholder:text-zinc-400 transition-colors hover:border-zinc-950/20 focus:border-zinc-950 focus:outline-none focus:ring-2 focus:ring-zinc-950/5"
				id={inputId}
			/>
		</div>
	);
};

export const ButtonComponent = (
	props: ButtonHTMLAttributes<HTMLButtonElement>,
) => {
	return (
		<button
			{...props}
			className="flex w-full cursor-pointer items-center justify-center rounded-lg bg-zinc-950 px-4 py-2.5 text-sm/6 font-semibold text-white shadow-sm transition-colors hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2 active:bg-zinc-700 disabled:cursor-default disabled:opacity-50"
		/>
	);
};

export const LinkComponent = (
	props: AnchorHTMLAttributes<HTMLAnchorElement>,
) => {
	return (
		<a
			{...props}
			className="font-medium text-zinc-950 underline decoration-zinc-950/30 underline-offset-2 transition-colors hover:decoration-zinc-950"
		/>
	);
};

export const ErrorComponent = ({ children }: { children: ReactNode }) => {
	return (
		<div
			className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm/6 text-red-900"
			role="alert"
		>
			{children}
		</div>
	);
};

export const SuccessComponent = ({ children }: { children: ReactNode }) => {
	return (
		<div
			className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm/6 text-green-900"
			role="alert"
		>
			{children}
		</div>
	);
};

export const Divider = () => {
	return <div className="h-px bg-zinc-950/10" />;
};
