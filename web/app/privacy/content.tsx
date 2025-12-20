import React from "react";
import fs from "fs/promises";
import path from "path";

import Footer from "@/components/Sections/Footer";
import MarkdownPolicyPage from "@/components/Sections/MarkdownPolicyPage";

/**
 * Renders the privacy notice page.
 *
 * Loads the privacy notice Markdown from src/components/Sections/privacy_notice.md and renders it inside MarkdownPolicyPage followed by the Footer.
 *
 * @returns A React element containing the rendered policy content and a footer.
 */
export default async function PrivacyPage() {
  const markdownPath = path.join(
    process.cwd(),
    "src",
    "components",
    "Sections",
    "privacy_notice.md",
  );
  const markdown = await fs.readFile(markdownPath, "utf8");

  return (
    <>
      <MarkdownPolicyPage markdown={markdown} />
      <Footer />
    </>
  );
}