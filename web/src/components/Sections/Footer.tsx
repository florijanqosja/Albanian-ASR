"use client";
import React from "react";
import styled from "styled-components";
import LogoImg from "../../assets/svg/Logo";
import { FaGithub, FaLinkedin } from "react-icons/fa";

export default function Contact() {
  return (
    <Wrapper>
      <div className="container mx-auto">
        <InnerWrapper className="flex justify-between items-center" style={{ padding: "30px 0" }}>
          <div className="flex items-center cursor-pointer" onClick={() => window.scrollTo(0, 0)}>
            <LogoContainer>
              <LogoImg />
            </LogoContainer>
            <h1 className="font-bold text-background text-lg" style={{ marginLeft: "15px" }}>
              DibraSpeaks
            </h1>
          </div>
          <SocialIconsAndTermsWrapper>
            <SocialIconsWrapper>
              <SocialIconLink href="https://github.com/florijanqosja" target="_blank" rel="noopener noreferrer">
                <FaGithub />
              </SocialIconLink>
              <SocialIconLink href="https://www.linkedin.com/in/florijan-qosja/" target="_blank" rel="noopener noreferrer">
                <FaLinkedin />
              </SocialIconLink>
            </SocialIconsWrapper>
            <TermsLink href="/termsandservices" className="text-background cursor-pointer text-sm mt-2 hover:text-primary transition-colors">
              Terms and Conditions
            </TermsLink>
          </SocialIconsAndTermsWrapper>
          <div 
            className="text-background cursor-pointer text-sm hover:text-primary transition-colors duration-300" 
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            Back to top
          </div>
        </InnerWrapper>
      </div>
    </Wrapper>
  );
}

const Wrapper = styled.div`
  width: 100%;
  background-color: var(--foreground);
`;

const InnerWrapper = styled.div`
  @media (max-width: 550px) {
    flex-direction: column;
  }
`;

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
`;

const SocialIconsAndTermsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
`;

const SocialIconsWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
`;

const SocialIconLink = styled.a`
  display: inline-block;
  margin: 0 10px;
  font-size: 1.5rem;
  color: var(--muted);
  transition: color 0.3s ease;

  &:hover {
    color: var(--primary);
  }
`;

const TermsLink = styled.a`
  text-decoration: none;
`;
