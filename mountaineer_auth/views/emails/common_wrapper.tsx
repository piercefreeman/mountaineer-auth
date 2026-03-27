import React from "react";
import { Tailwind } from "@react-email/tailwind";
import {
  Html,
  Head,
  Font,
  Body,
  Container,
  Section,
  Img,
  Row,
  Column,
  Text,
  Link,
} from "@react-email/components";

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
            webFont={{
              url: "https://fonts.gstatic.com/s/roboto/v27/KFOmCnqEu92Fr1Mu4mxKKTU1Kg.woff2",
              format: "woff2",
            }}
            fontWeight={400}
            fontStyle="normal"
          />
        </Head>
        <Body className="w-full">
          <Container className="mx-auto w-[580px] max-w-[580px]">
            <Section>
              {/* Header image */}
              {config.header_image && (
                <Row>
                  <Column align="center">
                    <Img
                      src={config.header_image}
                      alt={config.project_name}
                      width="40"
                      height="40"
                      className="mx-auto"
                    />
                  </Column>
                </Row>
              )}

              {/* Content container */}
              <Section className="mt-4 w-full text-sm text-gray-800">
                <Row>
                  <Column className="p-4">
                    <Text className="text-lg font-bold">{title}</Text>
                    {children}
                  </Column>
                </Row>
              </Section>

              {/* Footer */}
              <Section className="mt-4 w-full text-center text-xs text-slate-400">
                <Row>
                  <Column className="py-0">
                    <Text className="text-xs">
                      Sent by {config.project_name}, {config.project_address}.{" "}
                      <Link href={config.unsubscribe_url} className="underline">
                        Unsubscribe
                      </Link>
                    </Text>
                  </Column>
                </Row>
              </Section>
            </Section>
          </Container>
        </Body>
      </Html>
    </Tailwind>
  );
};

export default CommonWrapper;
