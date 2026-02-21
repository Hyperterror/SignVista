import type { Metadata } from 'next';
import { ClientLayout } from './components/ClientLayout';
import { SidebarProvider } from './context/SidebarContext';
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
      <body suppressHydrationWarning>
        <SidebarProvider>
          <ClientLayout>{children}</ClientLayout>
        </SidebarProvider>
      </body>
    </html>
  );
}
