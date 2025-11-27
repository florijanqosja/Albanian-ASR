"use client";
import React from "react";
// Sections
import Statistics from "../components/Sections/Statistics";
import Footer from "../components/Sections/Footer";
import AudioPlayer from "../components/Sections/AudioPlayer";

export default function Landing() {
  return (
    <>
      <AudioPlayer />
      <Statistics />
      <Footer />
    </>
  );
}
