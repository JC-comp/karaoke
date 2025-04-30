import type { Metadata } from "next";
import "./globals.css";
import 'react-toastify/dist/ReactToastify.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import { config } from '@fortawesome/fontawesome-svg-core'
config.autoAddCss = false
import '@fortawesome/fontawesome-svg-core/styles.css';
import BootstrapClient from '@/components/BootstrapClient';
import ThemeToggler from '@/components/ThemeToggler';
import { ToastContainer } from 'react-toastify';
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
        <Suspense>
          {children}
        </Suspense>
        <ThemeToggler />
        <ToastContainer
          theme='dark'
        />
      </body>
      <BootstrapClient />
    </html>
  );
}
