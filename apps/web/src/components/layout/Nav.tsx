"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { useUserStore } from "@/lib/store/user";

export function Nav() {
  const pathname = usePathname();
  const user = useUserStore((state) => state.user);

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/profile", label: "Profile" },
    { href: "/jobs", label: "Jobs" },
  ];

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-4 md:gap-6">
          <Link href="/" className="text-lg font-semibold">
            Resume Bot
          </Link>
          <div className="hidden gap-4 md:flex">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "text-sm font-medium transition-colors hover:text-primary",
                    isActive ? "text-foreground" : "text-muted-foreground"
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
        {user && (
          <div className="hidden text-sm text-muted-foreground sm:block">
            {user.first_name && user.last_name
              ? `${user.first_name} ${user.last_name}`
              : user.first_name || user.email || "User"}
          </div>
        )}
      </div>
    </nav>
  );
}

