"use client";
import * as React from "react";
import Image from "next/image";

function SvgComponent(props: any) {
  return (
    <Image src="/logo.png" alt="Logo" width={60} height={60} {...props} />
  );
}

export default SvgComponent;
