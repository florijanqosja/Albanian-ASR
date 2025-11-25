"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import LogoIcon from "../../assets/svg/Logo";

function NavList() {
  const pathname = usePathname();
  
  return (
    <ul className="mb-6 mt-4 flex flex-col gap-2 lg:mb-0 lg:mt-0 lg:flex-row lg:items-center lg:gap-6">
      <li className={`p-1 font-semibold ${pathname === "/" ? "text-primary" : "text-[#404040]"}`}>
        <Link href="/" className="flex items-center transition-colors hover:text-primary">
          Label
        </Link>
      </li>
      <li className={`p-1 font-semibold ${pathname === "/validate" ? "text-primary" : "text-[#404040]"}`}>
        <Link href="/validate" className="flex items-center transition-colors hover:text-primary">
          Validate
        </Link>
      </li>
      {/* <li className="p-1 font-bold text-gray-400 cursor-not-allowed">
        <span className="flex items-center">
          Try
        </span>
      </li>
      <li className="p-1 font-bold text-gray-400 cursor-not-allowed">
        <span className="flex items-center">
          Record
        </span>
      </li> */}
      <li className="p-1 font-semibold text-[#404040]">
        <a href={process.env.NEXT_PUBLIC_API_DOCS_URL || "#"} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-primary transition-colors">
          Docs
        </a>
      </li>
    </ul>
  );
}

export default function TopNavbar() {
  const [openNav, setOpenNav] = React.useState(false);
 
  React.useEffect(() => {
    window.addEventListener(
      "resize",
      () => window.innerWidth >= 960 && setOpenNav(false),
    );
  }, []);
 
  return (
    <nav className="mx-auto max-w-screen-xl px-4 py-3 bg-white shadow-md rounded-none lg:rounded-xl mt-2 border border-gray-200 sticky top-2 z-50">
      <div className="flex items-center justify-between lg:grid lg:grid-cols-3 text-[#404040]">
        <Link href="/" className="mr-4 cursor-pointer lg:ml-2 flex items-center gap-2 lg:justify-self-start">
            <div className="w-8 h-8">
                <LogoIcon />
            </div>
            <span className="font-bold text-lg mt-2">DibraSpeaks</span>
        </Link>
        <div className="hidden lg:block lg:justify-self-center">
          <NavList />
        </div>
        <div className="hidden gap-2 lg:flex lg:justify-self-end">
          <button className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-bold hover:bg-primary/90 transition-colors">Log In</button>
        </div>
        <button
          className="lg:hidden p-2 text-[#404040]"
          onClick={() => setOpenNav(!openNav)}
        >
          {openNav ? (
            <X className="h-6 w-6" strokeWidth={2} />
          ) : (
            <Menu className="h-6 w-6" strokeWidth={2} />
          )}
        </button>
      </div>
      <div className={`lg:hidden overflow-hidden transition-all duration-300 ${openNav ? "max-h-[1000px]" : "max-h-0"}`}>
        <NavList />
        <div className="flex w-full flex-nowrap items-center gap-2 mt-4 pb-4">
          <button className="w-full px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-bold hover:bg-primary/90 transition-colors">
            Log In
          </button>
        </div>
      </div>
    </nav>
  );
}
