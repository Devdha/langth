import type { Metadata } from "next";
import { Jua, Nanum_Gothic } from "next/font/google";
import "./globals.css";

const jua = Jua({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-jua",
});

const nanumGothic = Nanum_Gothic({
  weight: ["400", "700", "800"],
  subsets: ["latin"],
  variable: "--font-nanum",
});

export const metadata: Metadata = {
  title: "말놀이 자판기 | Talk-Talk Vending Machine",
  description: "즐거운 언어 재활을 위한 말놀이 자판기",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${jua.variable} ${nanumGothic.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
