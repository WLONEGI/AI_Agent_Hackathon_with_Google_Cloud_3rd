import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";

const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  variable: "--font-roboto",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Spell - AIストーリー生成サービス",
  description: "あなたの物語を素敵な漫画に変換するAIサービス。7つのフェーズで高品質な漫画を生成します。",
  keywords: "AI, 漫画, マンガ, 生成, ストーリー, イラスト, Spell",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <head>
        {/* Google Icons (Material Symbols) */}
        <link 
          rel="stylesheet" 
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" 
        />
        <link 
          rel="stylesheet" 
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" 
        />
      </head>
      <body
        className={`${roboto.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
