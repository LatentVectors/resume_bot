import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { Nav } from "@/components/layout/Nav";

export const metadata: Metadata = {
  title: "Resume Bot",
  description: "Resume and cover letter generation application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>
          <Nav />
          <main className="container mx-auto px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
