import React from "react";
import TopNavbar from "../components/Nav/TopNavbar";
import Statistics from "../components/Sections/Statistics";
import Footer from "../components/Sections/Footer"
import AudioValidater from "../components/Sections/Audiovalidate"

export default function Validate() {
  return (
    <>
      <TopNavbar />
      <AudioValidater />
      <Statistics />
      <Footer />
    </>
  );
}


