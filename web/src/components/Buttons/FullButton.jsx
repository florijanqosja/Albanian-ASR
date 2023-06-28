import React from "react";
import styled from "styled-components";

export default function FullButton({ title, action, border }) {
  return (
    <Wrapper
      className="animate pointer radius8"
      onClick={action ? () => action() : null}
      border={border}
    >
      {title}
    </Wrapper>
  );
}

const Wrapper = styled.button`
  border: 1px solid ${(props) => (props.border ? "#301616" : "#9E3936")};
  background-color: ${(props) => (props.border ? "transparent" : "#9E3936")};
  width: 100%;
  padding: 15px;
  outline: none;
  color: ${(props) => (props.border ? "#301616" : "#E1DDDD")};
  :hover {
    background-color: ${(props) => (props.border ? "transparent" : "#A99B9D")};
    border: 1px solid #9E3936;
    color: ${(props) => (props.border ? "#9E3936" : "#E1DDDD")};
  }
}
`;
