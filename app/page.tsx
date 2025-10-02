'use client';

import SubmissionForm from '@/components/SubmissionForm';
import { UserButton, SignedIn, SignedOut, RedirectToSignIn } from '@clerk/nextjs';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">AI Item Listing Generator</h1>
        <SignedIn>
          <UserButton afterSignOutUrl="/" />
          <SubmissionForm />
        </SignedIn>
        <SignedOut>
          <RedirectToSignIn />
        </SignedOut>
      </div>
    </main>
  );
}