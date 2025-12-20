import React from "react";
import fs from "fs/promises";
import path from "path";

import Footer from "@/components/Sections/Footer";
import MarkdownPolicyPage from "@/components/Sections/MarkdownPolicyPage";

/**
 * Renders the Terms and Services page by loading the terms markdown and composing it with the page footer.
 *
 * @returns A React element containing the rendered markdown policy content and the site footer.
 */
export default async function TermsAndServicesPage() {
  const markdownPath = path.join(
    process.cwd(),
    "src",
    "components",
    "Sections",
    "terms_and_services.md",
  );
  const markdown = await fs.readFile(markdownPath, "utf8");

  return (
    <>
      <MarkdownPolicyPage markdown={markdown} />
      <Footer />
    </>
  );
}