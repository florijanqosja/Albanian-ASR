import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  markdown: string;
};

/**
 * Render a styled policy page that displays the provided Markdown content.
 *
 * @param markdown - Markdown string to render inside the page
 * @returns A React element containing a styled container with the rendered Markdown
 */
export default function MarkdownPolicyPage({ markdown }: Props) {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-background text-foreground border border-border rounded-2xl p-6 md:p-10">
          <div className="policy-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}