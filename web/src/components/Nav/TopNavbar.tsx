"use client";
import React from "react";
import { Globe, Menu, X, LogOut, User, BarChart2 } from "lucide-react";
import { useSession, signOut } from "next-auth/react";
import { Avatar, Menu as MuiMenu, MenuItem, IconButton, Divider, ListItemIcon, Box, Tooltip, Button } from "@mui/material";
import { useTranslations, useLocale } from "next-intl";
import { Link, usePathname, useRouter, pathnames, locales } from "../../../i18n/routing";
import { useUserProfile } from "../../context/ProfileCompletionWrapper";
import LogoIcon from "../../assets/svg/Logo";

function NavList({ activePath }: { activePath: string }) {
    const t = useTranslations();

    const navItems: Array<{ name: string; path: keyof typeof pathnames; external?: boolean }> = [
        { name: t("nav.label"), path: "/" },
        { name: t("nav.validate"), path: "/validate" },
        { name: t("nav.record"), path: "/record" },
    ];

  return (
    <ul className="flex flex-col gap-2 lg:flex-row lg:items-center lg:gap-8 mb-0 mt-0">
      {navItems.map((item) => (
        <li key={item.name} className="p-1 font-medium text-sm uppercase tracking-wider">
                        {item.external ? (
                        <a 
                                href={item.path} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className="flex items-center text-gray-600 hover:text-primary transition-colors relative group"
                        >
                            {item.name}
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
                        </a>
                    ) : (
                        <Link 
                            href={item.path} 
                                className={`flex items-center transition-colors relative group ${activePath === item.path ? "text-primary font-bold" : "text-gray-600 hover:text-primary"}`}
                        >
                            {item.name}
                            <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${activePath === item.path ? "w-full" : "w-0 group-hover:w-full"}`}></span>
                        </Link>
                    )}
        </li>
      ))}
    </ul>
  );
}

export default function TopNavbar() {
    const t = useTranslations();
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();
    const basePathname = React.useMemo(() => {
        const segments = pathname.split("/").filter(Boolean);
        if (segments.length > 0 && locales.includes(segments[0] as (typeof locales)[number])) {
            const remainder = segments.slice(1).join("/");
            return remainder ? `/${remainder}` : "/";
        }
        return pathname || "/";
    }, [pathname]);
  const [openNav, setOpenNav] = React.useState(false);
  const { data: session, status } = useSession();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const openMenu = Boolean(anchorEl);
    const [langAnchorEl, setLangAnchorEl] = React.useState<null | HTMLElement>(null);
    const openLangMenu = Boolean(langAnchorEl);
    const userProfile = useUserProfile();
    const displayName = userProfile?.name ?? session?.user?.name;
    const displayEmail = session?.user?.email;
    const avatarSrc = userProfile?.avatar_url ?? session?.user?.image ?? undefined;

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

    const handleLangMenuClick = (event: React.MouseEvent<HTMLElement>) => {
        setLangAnchorEl(event.currentTarget);
    };

    const handleLangMenuClose = () => setLangAnchorEl(null);

    const handleLocaleChange = (nextLocale: string) => {
        // @ts-expect-error -- basePathname is a valid path but type inference fails here
        router.replace(basePathname, { locale: nextLocale });
        setLangAnchorEl(null);
    };
 
  React.useEffect(() => {
    window.addEventListener(
      "resize",
      () => window.innerWidth >= 960 && setOpenNav(false),
    );
  }, []);
 
  return (
    <Box sx={{ position: 'sticky', top: 16, zIndex: 50, px: 2 }}>
        <nav className="mx-auto max-w-screen-xl px-6 py-3 bg-white/90 backdrop-blur-md shadow-lg rounded-2xl border border-white/20 transition-all duration-300">
        <div className="flex items-center justify-between lg:grid lg:grid-cols-3 text-gray-800">
            <Link href="/" className="mr-4 cursor-pointer lg:ml-2 flex items-center gap-3 lg:justify-self-start group">
                <div className="w-10 h-10 text-primary transition-transform group-hover:scale-110 duration-300 drop-shadow-sm">
                    <LogoIcon />
                </div>
                                <span className="font-bold text-xl tracking-tight text-gray-900 group-hover:text-primary transition-colors">{t("common.appName")}</span>
            </Link>
            <div className="hidden lg:block lg:justify-self-center">
            <NavList activePath={basePathname} />
            </div>
            <div className="hidden gap-2 lg:flex lg:justify-self-end items-center">
                        <Tooltip title={t("common.language")}> 
                            <IconButton
                                onClick={handleLangMenuClick}
                                sx={{ border: '1px solid', borderColor: 'divider' }}
                                aria-label={t("common.language")}
                            >
                                <Globe size={18} />
                            </IconButton>
                        </Tooltip>
                        <MuiMenu
                            anchorEl={langAnchorEl}
                            open={openLangMenu}
                            onClose={handleLangMenuClose}
                            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                        >
                            <MenuItem selected={locale === "en"} onClick={() => handleLocaleChange("en")}>
                                {t("common.english")}
                            </MenuItem>
                            <MenuItem selected={locale === "sq"} onClick={() => handleLocaleChange("sq")}>
                                {t("common.albanian")}
                            </MenuItem>
                        </MuiMenu>
            {status === "loading" ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ width: 120, height: 40, bgcolor: 'grey.200', borderRadius: 2, animation: 'pulse 1.5s ease-in-out infinite', '@keyframes pulse': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.5 } } }} />
                  <Box sx={{ width: 40, height: 40, bgcolor: 'grey.200', borderRadius: '50%', animation: 'pulse 1.5s ease-in-out infinite' }} />
                </Box>
            ) : session ? (
                <>
                <div className="flex flex-col items-end mr-3">
                    <span className="text-sm font-bold text-gray-900 leading-tight">{displayName}</span>
                    <span className="text-xs text-gray-500">{displayEmail}</span>
                </div>
                <IconButton 
                    onClick={handleMenuClick} 
                    size="small" 
                    sx={{ 
                        ml: 0.5,
                        border: '2px solid',
                        borderColor: 'primary.light',
                        padding: '2px',
                        transition: 'all 0.2s',
                        '&:hover': { borderColor: 'primary.main', transform: 'scale(1.05)', boxShadow: '0 0 0 4px rgba(166, 77, 74, 0.1)' }
                    }}
                >
                    <Avatar 
                        src={avatarSrc}
                        alt={displayName || "User"}
                        sx={{ width: 38, height: 38, bgcolor: 'primary.main' }}
                    >
                        {displayName?.[0] || "U"}
                    </Avatar>
                </IconButton>
                <MuiMenu
                    anchorEl={anchorEl}
                    open={openMenu}
                    onClose={handleMenuClose}
                    onClick={handleMenuClose}
                    transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                    anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                    PaperProps={{
                        elevation: 0,
                        sx: {
                        overflow: 'visible',
                        filter: 'drop-shadow(0px 4px 20px rgba(0,0,0,0.1))',
                        mt: 1.5,
                        borderRadius: 3,
                        minWidth: 220,
                        border: '1px solid',
                        borderColor: 'divider',
                        '& .MuiAvatar-root': {
                            width: 32,
                            height: 32,
                            ml: -0.5,
                            mr: 1,
                        },
                        '&:before': {
                            content: '""',
                            display: 'block',
                            position: 'absolute',
                            top: 0,
                            right: 24,
                            width: 10,
                            height: 10,
                            bgcolor: 'background.paper',
                            transform: 'translateY(-50%) rotate(45deg)',
                            zIndex: 0,
                            borderTop: '1px solid',
                            borderLeft: '1px solid',
                            borderColor: 'divider',
                        },
                        },
                    }}
                >
                    <Box sx={{ px: 2.5, py: 1.5, bgcolor: 'grey.50', mb: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
                        <p className="text-sm font-bold text-gray-900 truncate">{displayName}</p>
                        <p className="text-xs text-gray-500 truncate">{displayEmail}</p>
                    </Box>
                    <Link href="/my-labels" passHref>
                        <MenuItem onClick={handleMenuClose} sx={{ py: 1.5, px: 2.5, mx: 1, borderRadius: 1 }}>
                            <ListItemIcon>
                                <BarChart2 size={18} />
                            </ListItemIcon>
                                {t("nav.dashboard")}
                        </MenuItem>
                    </Link>
                    <Link href="/profile" passHref>
                        <MenuItem onClick={handleMenuClose} sx={{ py: 1.5, px: 2.5, mx: 1, borderRadius: 1 }}>
                            <ListItemIcon>
                                <User size={18} />
                            </ListItemIcon>
                                {t("nav.profile")}
                        </MenuItem>
                    </Link>
                    <Divider sx={{ my: 1 }} />
                    <MenuItem onClick={() => signOut()} sx={{ py: 1.5, px: 2.5, mx: 1, borderRadius: 1, color: 'error.main', '&:hover': { bgcolor: 'error.lighter' } }}>
                    <ListItemIcon sx={{ color: 'error.main' }}>
                        <LogOut size={18} />
                    </ListItemIcon>
                        {t("nav.logout")}
                    </MenuItem>
                </MuiMenu>
                </>
            ) : (
                <div className="flex gap-3">
                    <Link href="/login" className="px-6 py-2.5 text-sm font-bold text-gray-700 hover:text-primary hover:bg-gray-50 rounded-full transition-all">
                        {t("nav.login")}
                </Link>
                    <Link href="/login" className="px-6 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-primary to-[#FF8E53] hover:shadow-lg hover:scale-105 rounded-full transition-all duration-300">
                        {t("nav.signup")}
                </Link>
                </div>
            )}
            </div>
            <IconButton
            className="ml-auto h-6 w-6 text-inherit hover:bg-transparent focus:bg-transparent active:bg-transparent lg:hidden"
            onClick={() => setOpenNav(!openNav)}
            >
            {openNav ? (
                <X className="h-6 w-6" strokeWidth={2} />
            ) : (
                <Menu className="h-6 w-6" strokeWidth={2} />
            )}
            </IconButton>
        </div>
        {/* Mobile Nav */}
        <div className={`lg:hidden transition-all duration-300 ease-in-out overflow-hidden ${openNav ? "max-h-[500px] opacity-100 mt-4" : "max-h-0 opacity-0"}`}>
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                <NavList activePath={basePathname} />
                                <div className="flex items-center gap-3 mt-3">
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        startIcon={<Globe size={16} />}
                                        onClick={(event) => setLangAnchorEl(event.currentTarget)}
                                        sx={{ textTransform: 'none', fontWeight: 700, borderRadius: 2 }}
                                    >
                                        {locale === "sq" ? t("common.albanian") : t("common.english")}
                                    </Button>
                                </div>
                {status === "loading" ? (
                    <div className="flex flex-col gap-2 mt-4 border-t border-gray-200 pt-4">
                        <Box sx={{ width: '100%', height: 60, bgcolor: 'grey.200', borderRadius: 2, animation: 'pulse 1.5s ease-in-out infinite' }} />
                        <Box sx={{ width: '100%', height: 40, bgcolor: 'grey.200', borderRadius: 2, animation: 'pulse 1.5s ease-in-out infinite' }} />
                    </div>
                ) : session ? (
                    <div className="flex flex-col gap-2 mt-4 border-t border-gray-200 pt-4">
                        <div className="flex items-center gap-3 mb-4 p-2 bg-white rounded-lg shadow-sm">
                            <Avatar src={avatarSrc} sx={{ width: 40, height: 40 }} />
                            <div className="overflow-hidden">
                                <p className="font-bold text-sm truncate">{displayName}</p>
                                <p className="text-xs text-gray-500 truncate">{displayEmail}</p>
                            </div>
                        </div>
                        <Link href="/my-labels" className="p-3 hover:bg-white hover:shadow-sm rounded-lg flex items-center gap-3 text-gray-700 transition-all">
                            <BarChart2 size={18} className="text-primary" /> {t("nav.dashboard")}
                        </Link>
                        <Link href="/profile" className="p-3 hover:bg-white hover:shadow-sm rounded-lg flex items-center gap-3 text-gray-700 transition-all">
                            <User size={18} className="text-primary" /> {t("nav.profile")}
                        </Link>
                        <button onClick={() => signOut()} className="p-3 hover:bg-red-50 text-red-600 rounded-lg text-left flex items-center gap-3 transition-all mt-2">
                            <LogOut size={18} /> {t("nav.logout")}
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3 mt-6">
                        <Link href="/login" className="w-full text-center py-3 border border-gray-200 text-gray-700 rounded-xl font-bold hover:bg-white transition-all">
                            {t("nav.login")}
                        </Link>
                        <Link href="/login" className="w-full text-center py-3 bg-primary text-white rounded-xl font-bold shadow-md hover:shadow-lg transition-all">
                            {t("nav.signup")}
                        </Link>
                    </div>
                )}
            </div>
        </div>
        </nav>
    </Box>
  );
}
