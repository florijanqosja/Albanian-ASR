"use client";
import React from "react";
import styled from "styled-components";
import { useTranslations } from "next-intl";
import { Link } from "../../../i18n/routing";
// Assets
import CloseIcon from "../../assets/svg/CloseIcon";
import LogoIcon from "../../assets/svg/Logo";

interface SidebarProps {
  sidebarOpen: boolean;
  toggleSidebar: (open: boolean) => void;
}

export default function Sidebar({ sidebarOpen, toggleSidebar }: SidebarProps) {
  const t = useTranslations();
  return (
    <Wrapper className="bg-foreground transition-all duration-300" $sidebarOpen={sidebarOpen}>
      <SidebarHeader className="flex justify-between items-center">
        <div className="flex items-center">
          <LogoIcon />
          <h1 className="text-primary-foreground text-xl font-bold" style={{ marginLeft: "15px" }}>
            {t("common.appName")}
          </h1>
        </div>
        <CloseBtn onClick={() => toggleSidebar(!sidebarOpen)} className="cursor-pointer text-primary-foreground">
          <CloseIcon />
        </CloseBtn>
      </SidebarHeader>
      <UlStyle className="flex flex-col items-center">
        <li className="font-semibold text-lg cursor-pointer my-4">
          <Link
            onClick={() => toggleSidebar(!sidebarOpen)}
            className="text-primary-foreground p-4"
            href="/"
          >
            {t("nav.label")}
          </Link>
        </li>
        <li className="font-semibold text-lg cursor-pointer my-4">
          <Link
            onClick={() => toggleSidebar(!sidebarOpen)}
            className="text-primary-foreground p-4"
            href="/validate"
          >
            {t("nav.validate")}
          </Link>
        </li>
        <li className="font-semibold text-lg cursor-pointer my-4">
          <Link
            onClick={() => toggleSidebar(!sidebarOpen)}
            className="text-primary-foreground p-4"
            href="/record"
          >
            {t("nav.record")}
          </Link>
        </li>
      </UlStyle>
    </Wrapper>
  );
}

const Wrapper = styled.nav<{ $sidebarOpen: boolean }>`
  width: 400px;
  height: 100vh;
  position: fixed;
  top: 0;
  padding: 0 30px;
  right: ${(props) => (props.$sidebarOpen ? "0px" : "-400px")};
  z-index: 9999;
  @media (max-width: 400px) {
    width: 100%;
  }
`;

const SidebarHeader = styled.div`
  padding: 20px 0;
`;

const CloseBtn = styled.button`
  border: 0px;
  outline: none;
  background-color: transparent;
  padding: 10px;
`;

const UlStyle = styled.ul`
  padding: 40px;
`;
