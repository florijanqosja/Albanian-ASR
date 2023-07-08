import React from "react";
import styled from "styled-components";
import { Link } from "react-scroll";
// Assets
import LogoImg from "../../assets/svg/Logo";
import { FaGithub, FaLinkedin } from "react-icons/fa";

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
          <SocialIconsWrapper>
            <SocialIconLink href="https://github.com/florijanqosja" target="_blank" rel="noopener noreferrer">
              <FaGithub />
            </SocialIconLink>
            <SocialIconLink href="https://www.linkedin.com/in/florijan-qosja/" target="_blank" rel="noopener noreferrer">
              <FaLinkedin />
            </SocialIconLink>
          </SocialIconsWrapper>
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
