import React from "react";
import { Helmet } from "react-helmet";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
// Screens
import Landing from "./screens/Landing.jsx";
import Validate from "./screens/Validate.jsx";
import TermsAndServices from "./screens/TermsAndServices.jsx";
import Transcribe from "./screens/Transcribe.jsx";

export default function App() {
  return (
    <>
      <Helmet>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link href="https://fonts.googleapis.com/css2?family=Khula:wght@400;600;800&display=swap" rel="stylesheet" />
      </Helmet>
      <Router>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/validate" element={<Validate />} />
          <Route path="/termsandservices" element={<TermsAndServices />} />
          <Route path="/transcribe" element={<Transcribe />} />
        </Routes>
      </Router>
    </>
  );
}
