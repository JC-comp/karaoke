import type { Metadata } from "next";

import 'bootstrap/dist/css/bootstrap.min.css';
import 'react-toastify/dist/ReactToastify.css';
import "./globals.css";

import { config } from '@fortawesome/fontawesome-svg-core'
import '@fortawesome/fontawesome-svg-core/styles.css'
config.autoAddCss = false

import BootstrapClient from '@/components/BootstrapClient';
import { ThemeProvider } from '@/contexts/theme/ThemeContext';
import ThemeConsumerLayout from '@/components/layout/ThemeConsumerLayout';
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "JTV",
  description: "A karaoke generator that creates karaoke videos from YouTube links or local files.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-bs-theme="dark">
      <body>
        <ThemeProvider>
          <ThemeConsumerLayout>
            <Suspense>
              {children}
            </Suspense>
          </ThemeConsumerLayout>
        </ThemeProvider>
      </body>
      <BootstrapClient />
    </html>
  );
}
