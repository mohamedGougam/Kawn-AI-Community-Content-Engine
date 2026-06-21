import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata: Metadata = {
  title: 'Kawn AI Community Content Engine',
  description: 'AI-powered content generation for community posts',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <Sidebar />
          <main className="ml-64 min-h-screen p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
