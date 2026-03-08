'use client';

import { useState, useEffect, useMemo } from 'react';
import { useTheme } from '@/contexts/theme/ThemeContext';
import styles from './ThemeToggler.module.css';

export default function ThemeToggler() {
    const { theme, toggleTheme } = useTheme();
    const [isAtTop, setIsAtTop] = useState(true);
    
    const buttonClasses = useMemo(() => {
        const variant = theme === 'dark' ? 'btn-outline-info' : 'btn-outline-dark';
        const visibility = isAtTop ? styles.visible : styles.hidden;
        return `btn btn-lg ${variant} ${styles.toggleBtn} ${visibility}`;
    }, [theme, isAtTop]);

    // Handle Scroll Visibility
    useEffect(() => {
        const handleScroll = () => {
            const atTop = window.scrollY < 10;
            if (isAtTop !== atTop) setIsAtTop(atTop);
        };

        window.addEventListener("scroll", handleScroll, { passive: true });
        return () => window.removeEventListener("scroll", handleScroll);
    }, [isAtTop]);

    return (
        <button
            onClick={toggleTheme}
            className={buttonClasses}
        >
            {theme === 'dark' ? '🌙 Dark' : '☀️ Light'}
        </button>
    );
}
