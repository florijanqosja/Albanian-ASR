import React from "react";
import TopNavbar from "../components/Nav/TopNavbar";
import Pricing from "../components/Sections/Pricing";
import Footer from "../components/Sections/Footer"
import AudioTranscriber from "../components/Sections/AudioTranscriber"

export default function Validate() {
  return (
    <>
      <TopNavbar />
      <AudioTranscriber />
      <Pricing />
      <Footer />
    </>
  );
}


