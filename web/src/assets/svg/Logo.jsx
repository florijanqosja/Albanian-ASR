import * as React from "react";
import Logo from "../../assets/logo/logo.png";

function SvgComponent(props) {
  return (
    <img src={Logo} alt="Logo" width={60} height={60} viewBox="0 0 27 40" {...props} />
  );
}

export default SvgComponent;
