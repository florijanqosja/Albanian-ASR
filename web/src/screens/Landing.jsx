import React from "react";
// Sections
import TopNavbar from "../components/Nav/TopNavbar";
import Pricing from "../components/Sections/Pricing";
import Footer from "../components/Sections/Footer"
import AudioPlayer from "../components/Sections/Audioplayer"

export default function Landing() {
  return (
    <>
      <TopNavbar />
      <AudioPlayer />
      <Pricing />
      <Footer />
    </>
  );
}


