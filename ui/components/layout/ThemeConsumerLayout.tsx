"use client";

import { ToastContainer } from 'react-toastify';
import { useTheme } from '@/contexts/theme/ThemeContext';

export default function ThemedLayoutContent({ children }: { children: React.ReactNode }) {
    const { theme } = useTheme();

    return (
        <>
            {children}
            <ToastContainer theme={theme} />
        </>
    );
}