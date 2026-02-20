import type { Metadata } from 'next';
import { ThemeProvider } from './context/ThemeContext';
import { Sidebar } from './components/Sidebar';
import { LoadingScreen } from './components/LoadingScreen';
import { Toaster } from './components/Toaster';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'SignVista',
  description: 'Sign Language Learning Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <div className="flex min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-colors duration-300">
            <Toaster />
            <Sidebar />
            <main className="flex-1 ml-0 lg:ml-[20%] overflow-x-hidden">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
