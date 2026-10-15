import React, { createContext, useContext, useState, useEffect } from 'react';

interface NavContextType {
  isMobileOpen: boolean;
  openMobileNav: () => void;
  closeMobileNav: () => void;
  toggleMobileNav: () => void;
}

const NavContext = createContext<NavContextType>({
  isMobileOpen: false,
  openMobileNav: () => {},
  closeMobileNav: () => {},
  toggleMobileNav: () => {},
});

export const NavProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const openMobileNav = () => setIsMobileOpen(true);
  const closeMobileNav = () => setIsMobileOpen(false);
  const toggleMobileNav = () => setIsMobileOpen((prev) => !prev);

  // Close drawer on escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileOpen) {
        closeMobileNav();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileOpen]);

  // Lock background scroll when drawer is open on mobile
  useEffect(() => {
    if (isMobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileOpen]);

  // Close drawer automatically on window resize to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024 && isMobileOpen) {
        setIsMobileOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobileOpen]);

  return (
    <NavContext.Provider
      value={{
        isMobileOpen,
        openMobileNav,
        closeMobileNav,
        toggleMobileNav,
      }}
    >
      {children}
    </NavContext.Provider>
  );
};

export const useNav = () => useContext(NavContext);
