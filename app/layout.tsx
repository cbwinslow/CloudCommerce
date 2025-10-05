import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ClerkProvider } from '@clerk/nextjs';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Item Listing Generator - Create Marketplace Listings with AI',
  description: 'Transform your items into professional marketplace listings using AI. Upload images, get AI-powered analysis, and generate optimized listings for eBay, Amazon, Facebook Marketplace and more.',
  keywords: 'AI listing generator, marketplace listings, eBay listings, Amazon listings, AI product description, automated listings',
  authors: [{ name: 'AI Listing Generator' }],
  openGraph: {
    title: 'AI Item Listing Generator',
    description: 'Create professional marketplace listings with AI-powered analysis',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI Item Listing Generator',
    description: 'Create professional marketplace listings with AI-powered analysis',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${inter.className} antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
