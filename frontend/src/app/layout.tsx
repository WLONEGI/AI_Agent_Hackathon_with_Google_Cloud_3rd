import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Manga Generator - AI漫画生成サービス",
  description: "あなたの物語を素敵な漫画に変換するAIサービス。7つのフェーズで高品質な漫画を生成します。",
  keywords: "AI, 漫画, マンガ, 生成, ストーリー, イラスト",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className={`${inter.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
