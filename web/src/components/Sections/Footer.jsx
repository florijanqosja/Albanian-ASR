import React from "react";
import styled from "styled-components";
import { Link } from "react-scroll";
import LogoImg from "../../assets/svg/Logo";
import { FaGithub, FaLinkedin, FaCoffee } from "react-icons/fa";

export default function Contact() {
  return (
    <Wrapper>
      <div className="container">
        <InnerWrapper className="flexSpaceCenter" style={{ padding: "30px 0" }}>
          <div className="flexCenter animate pointer" onClick={() => window.scrollTo(0, 0)}>
            <LogoContainer>
              <LogoImg />
            </LogoContainer>
            <h1 className="font15 extraBold whiteColor" style={{ marginLeft: "15px" }}>
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
              <SocialIconLink href="https://www.buymeacoffee.com/florijanqosja" target="_blank" rel="noopener noreferrer">
                <FaCoffee />
              </SocialIconLink>
            </SocialIconsWrapper>
            <TermsLink href="/termsandservices" className="whiteColor animate pointer font13">
              Terms and Conditions
            </TermsLink>
          </SocialIconsAndTermsWrapper>
          <div className="whiteColor animate pointer font13" onClick={() => window.scrollTo(0, 0)}>
            Back to top
          </div>
        </InnerWrapper>
      </div>
    </Wrapper>
  );
}

const Wrapper = styled.div`
  width: 100%;
  background-color: #301616;
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
  font-size: 24px;
  color: #e1dddd;
  transition: color 0.3s ease;

  &:hover {
    color: #9e3936;
  }
`;

const TermsLink = styled.a`
  margin-top: 10px;
  text-decoration: none;
  color: #e1dddd;
  transition: color 0.3s ease;

  &:hover {
    color: #9e3936;
  }
`;
