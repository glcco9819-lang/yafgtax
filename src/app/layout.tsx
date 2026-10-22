import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "سامانه مدیریت دفتر حسابداری",
  description: "سامانه مدیریت عملیات دفاتر حسابداری - کنترل تسک، گزارش کار و ارزیابی پرسنل",
  keywords: ["حسابداری", "دفتر حسابداری", "تسک", "مدیریت", "ارزیابی پرسنل"],
  authors: [{ name: "Z.ai" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <body className="antialiased bg-background text-foreground font-sans">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
