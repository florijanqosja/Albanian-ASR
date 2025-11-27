"use client";
import React from "react";
import styled from "styled-components";

interface BackdropProps {
  toggleSidebar: (open: boolean) => void;
}

export default function Backdrop({ toggleSidebar }: BackdropProps) {
  return <Wrapper className="bg-black opacity-80" onClick={() => toggleSidebar(false)}></Wrapper>;
}

const Wrapper = styled.div`
  width: 100%;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 99;
`;
