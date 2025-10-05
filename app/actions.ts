'use server';

import { revalidatePath } from 'next/cache';
import { submitItem } from '@/lib/backend';  // Import backend function (adapt from FastAPI)

export async function submitAction(formData: FormData) {
  'use server';
  const images = formData.getAll('images') as File[];
  const summary = formData.get('summary') as string;
  const category = formData.get('category') as string;
  const condition = formData.get('condition') as string;

  // Call backend (fetch to FastAPI /submit)
  const response = await fetch('http://localhost:8000/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ images: images.map(f => f.name), summary, category, condition }),  // Send URLs after upload
  });

  if (!response.ok) throw new Error('Submission failed');

  const result = await response.json();
  revalidatePath('/submit');
  return result;
}