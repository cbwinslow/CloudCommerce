// CrewAI integration (Python via API call to backend)
export async function runCrewAI(images: string[], summary: string, category?: string, condition?: string) {
  const response = await fetch('http://localhost:8000/crew', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ images, summary, category, condition }),
  });
  return response.json();
}

// In production, deploy backend as Vercel function or separate service
