"use client";
import React from "react";
// Sections
import TopNavbar from "@/components/Nav/TopNavbar";
import Statistics from "@/components/Sections/Statistics";
import Footer from "@/components/Sections/Footer";
import AudioValidate from "@/components/Sections/AudioValidate";

export default function Validate() {
  return (
    <>
      <TopNavbar />
      <AudioValidate />
      <Statistics />
      <Footer />
    </>
  );
}
