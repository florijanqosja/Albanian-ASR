import React from "react";
import TopNavbar from "../components/Nav/TopNavbar";
import Pricing from "../components/Sections/Pricing";
import Footer from "../components/Sections/Footer"
import AudioValidater from "../components/Sections/Audiovalidate"

export default function Validate() {
  return (
    <>
      <TopNavbar />
      <AudioValidater />
      <Pricing />
      <Footer />
    </>
  );
}


