"use client";
import React from 'react';
import { useEffect } from 'react';

export default function ThemeToggler() {
  const toggleTheme = (e: React.MouseEvent<HTMLButtonElement>) => {
    const button = e.target as HTMLElement;
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    button.innerText = newTheme === 'dark' ? '🌙 Dark' : '☀️ Light';
    button.classList.toggle('btn-outline-info');
    button.classList.toggle('btn-light');
  };

  const handleScroll = () => {
    const button = document.querySelector('.theme-toggle') as HTMLButtonElement;
    if (window.scrollY > 0) {
      if (!button.classList.contains('transitioning')) {
        if (button.classList.contains('d-none'))
          return;
        button.classList.add('transitioning');
        button.classList.remove('showing');
        setTimeout(() => {
          button.classList.add('d-none')
          button.classList.remove('transitioning');
        }, 150);
      }
    } else {
      if (!button.classList.contains('transitioning')) {
        button.classList.add('transitioning');
        button.classList.remove('d-none')
        setTimeout(() => {
          button.classList.add('showing');
          button.classList.remove('transitioning');
        }, 150);
      }
    }
  };

  useEffect(() => {
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <button onClick={toggleTheme} className={'btn btn-outline-info btn-lg theme-toggle showing'}>
      🌙 Dark
    </button>
  );
}