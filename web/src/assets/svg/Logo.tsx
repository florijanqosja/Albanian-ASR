"use client";
import * as React from "react";
import Image, { ImageProps } from "next/image";

function SvgComponent(props: Omit<ImageProps, "src" | "alt">) {
  return (
    <Image src="/logo.png" alt="Logo" width={60} height={60} {...props} />
  );
}

export default SvgComponent;
