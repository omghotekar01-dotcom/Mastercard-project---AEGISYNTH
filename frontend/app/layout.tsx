import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "AEGISYNTH | Autonomous Payment Defence Compiler",
  description: "Compile zero-day payment attacks into verified defence policies.",
};
export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body>{children}</body></html>;
}
