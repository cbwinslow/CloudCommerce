'use client';

import SubmissionForm from '@/components/SubmissionForm';
import { UserButton, SignedIn, SignedOut } from '@clerk/nextjs';
import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">AI Item Listing Generator</h1>
            <p className="text-lg text-gray-600">Transform images into marketplace-ready listings with AI</p>
          </div>
          <SignedIn>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
          <SignedOut>
            <div className="space-x-4">
              <Link
                href="/sign-in"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Sign In
              </Link>
              <Link
                href="/sign-up"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
              >
                Sign Up
              </Link>
            </div>
          </SignedOut>
        </header>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Form Section */}
          <div className="lg:col-span-2">
            <SignedIn>
              <SubmissionForm />
            </SignedIn>
            <SignedOut>
              <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                  Welcome to AI Item Listing Generator
                </h2>
                <p className="text-gray-600 mb-6">
                  Sign up or sign in to start creating AI-powered marketplace listings from your images.
                </p>
                <div className="space-y-3">
                  <Link
                    href="/sign-up"
                    className="block w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium"
                  >
                    Get Started Free
                  </Link>
                  <Link
                    href="/sign-in"
                    className="block w-full text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Already have an account? Sign In
                  </Link>
                </div>
              </div>
            </SignedOut>
          </div>

          {/* Features Section */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">✨ Features</h3>
              <ul className="space-y-3 text-sm text-gray-600">
                <li>• AI-powered item analysis</li>
                <li>• Multi-platform listing generation</li>
                <li>• Image upload and optimization</li>
                <li>• CSV export for bulk upload</li>
                <li>• Mobile app support</li>
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 How it works</h3>
              <ol className="space-y-2 text-sm text-gray-600">
                <li>1. Upload images of your item</li>
                <li>2. Add a description or summary</li>
                <li>3. AI analyzes and generates listings</li>
                <li>4. Export to CSV or copy directly</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
