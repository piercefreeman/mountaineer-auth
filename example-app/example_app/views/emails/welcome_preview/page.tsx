import React from "react";
import { Tailwind } from "@react-email/tailwind";

import { useServer } from "./_server";

const Page = () => {
  const serverState = useServer();

  return (
    <Tailwind>
      <div className="bg-[#f4efe8] px-6 py-10 font-sans text-[#1f2937]">
        <div className="mx-auto max-w-[600px] overflow-hidden rounded-[28px] bg-white">
          <div className="bg-[#1f3b57] px-10 py-9 text-white">
            <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.35em] text-[#f5d7a1]">
              Mountaineer Email
            </p>
            <h1 className="m-0 mt-4 text-[32px] font-semibold leading-[38px]">
              A Tailwind email preview with live server data.
            </h1>
            <p className="m-0 mt-4 text-[15px] leading-7 text-[#d9e2ec]">
              Use the admin panel payload form to change the recipient name and
              see the rendered email update instantly.
            </p>
          </div>

          <div className="px-10 py-10">
            <p className="m-0 text-[16px] leading-7">
              Hi <span className="font-semibold">{serverState.recipient_name}</span>,
            </p>
            <p className="m-0 mt-4 text-[16px] leading-7 text-[#4b5563]">
              This sample template is wired into the real example app so you can
              test the full admin preview flow while iterating on
              <span className="font-semibold text-[#111827]">
                {" "}
                mountaineer_auth
              </span>
              .
            </p>

            <div className="mt-8 rounded-[24px] bg-[#f9f6f1] px-6 py-6">
              <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.25em] text-[#9a7b4f]">
                Preview Scenario
              </p>
              <p className="m-0 mt-3 text-[22px] font-semibold leading-[30px] text-[#1f2937]">
                Personalize this message from the email admin console.
              </p>
              <p className="m-0 mt-3 text-[15px] leading-7 text-[#6b7280]">
                The name above comes from the server-rendered payload, not from
                client state, so this mirrors how production email renders are
                injected.
              </p>
            </div>

            <a
              href="https://resend.com"
              className="mt-8 inline-block rounded-full bg-[#111827] px-6 py-3 text-[14px] font-semibold text-white no-underline"
            >
              Review Delivery Options
            </a>

            <p className="m-0 mt-8 text-[13px] leading-6 text-[#9ca3af]">
              Sent from the local example app preview environment.
            </p>
          </div>
        </div>
      </div>
    </Tailwind>
  );
};

export default Page;
