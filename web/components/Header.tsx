"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { useState, useEffect } from "react";

const navItems = [
  { href: "/chat", label: "Chat" },
  { href: "/library", label: "Library" },
  { href: "/ingest", label: "Ingest" },
  { href: "/eval", label: "Eval" },
];

export default function Header() {
  const pathname = usePathname();
  const { data: session, status } = useSession();
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 10);
    }
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    function handleClickOutside() {
      setMenuOpen(false);
    }
    if (menuOpen) {
      document.addEventListener("click", handleClickOutside);
    }
    return () => document.removeEventListener("click", handleClickOutside);
  }, [menuOpen]);

  if (status === "loading") {
    return (
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "glass py-3" : "bg-transparent py-4"
      }`}>
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="font-semibold text-lg tracking-tight">Nexus Local RAG</span>
          </div>
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      </header>
    );
  }

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? "glass py-3" : "bg-transparent py-4"
    }`}>
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link 
            href="/chat" 
            className="font-semibold text-lg tracking-tight hover:opacity-80 transition-opacity"
          >
            Nexus Local RAG
          </Link>
          <nav className="flex gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== "/chat" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                    isActive 
                      ? "bg-primary/10 text-primary" 
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {session ? (
            <div className="relative" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 text-sm hover:opacity-80 transition-opacity"
              >
                <span className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center text-primary text-xs font-medium">
                  {session.user?.name?.charAt(0) || "U"}
                </span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 card shadow-lg py-2 z-50 animate-slide-up">
                  <div className="px-4 py-2 text-xs text-muted-foreground border-b border-border">
                    {session.user?.email || "Nexus User"}
                  </div>
                  <button
                    onClick={() => signOut({ callbackUrl: "/login" })}
                    className="w-full text-left px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="btn btn-primary text-sm"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
