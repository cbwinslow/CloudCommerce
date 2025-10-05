import React from 'react';
import Head from 'next/head';
import { Header } from './Header';
import { Footer } from './Footer';
import { OctopusMascot } from '../ui/OctopusMascot';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  title = 'CloudCommerce - AI-Powered E-commerce Platform',
  description = 'Transform your e-commerce experience with AI-powered tools for product listings, inventory management, and sales optimization.',
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-slate-50 to-purple-50 dark:from-slate-900 dark:to-gray-900">
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header />
      
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      
      <Footer />
      
      {/* Floating Octopus Mascot */}
      <div className="fixed bottom-8 right-8 z-50 hidden md:block">
        <OctopusMascot />
      </div>
    </div>
  );
};

export default MainLayout;
