"use client";

import React from "react";
import Footer from "@/components/Sections/Footer";
import ReportMisuse from "@/components/Sections/ReportMisuse";

/**
 * Page component that renders the report misuse section followed by the site footer.
 *
 * @returns A React element containing the ReportMisuse section and the Footer
 */
export default function ReportPage() {
  return (
    <>
      <ReportMisuse />
      <Footer />
    </>
  );
}