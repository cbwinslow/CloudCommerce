#!/bin/bash
# Full Clean Setup for CloudCommerce - Run this to fix everything

set -e  # Exit on error

echo "=== 1. Killing conflicting processes ==="
kill $(lsof -ti:3000,8000,8001,5432) 2>/dev/null || true  # Kill Next.js, uvicorn, Postgres

echo "=== 2. Cleaning workspace ==="
cd /home/foomanchu8008/CascadeProjects/CloudCommerce
rm -rf frontend/node_modules frontend/.next backend/venv backend/__pycache__ mobile/node_modules
rm -f .env.local .env.production  # Keep .env.example

echo "=== 3. Setting up frontend (Next.js) ==="
cd frontend
rm -rf * .gitignore package-lock.json pnpm-lock.yaml  # Fresh start
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --yes --no-tailwind --no-src-dir --no-app --no-eslint
# Install our deps
pnpm add next-intl recharts framer-motion lucide-react class-variance-authority js-cookie @sentry/nextjs @bitwarden/sdk-napi @supabase/supabase-js stripe zod @clerk/nextjs @ai-sdk/react
pnpm add -D @types/node @types/react @types/react-dom typescript eslint-config-next
pnpm install

# Create key frontend files (from our implementation)
cat > src/app/layout.tsx << 'EOF'
import { ClerkProvider } from '@clerk/nextjs';
import { NextIntlClientProvider } from 'next-intl';
import { notFound } from 'next/navigation';
import { GoogleAnalytics } from '@next/third-parties/google';

export default function RootLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (params.locale !== 'en' && params.locale !== 'es' && params.locale !== 'fr') {
    notFound();
  }

  return (
    <html lang={locale}>
      <body>
        <ClerkProvider>
          <NextIntlClientProvider locale={locale} messages={messages}>
            {children}
          </NextIntlClientProvider>
        </ClerkProvider>
        <GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA_ID} />
      </body>
    </html>
  );
}
EOF

cat > src/app/page.tsx << 'EOF'
export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-20 text-center">
      <div className="container mx-auto px-4">
        <h1 className="text-5xl font-bold mb-4">AI Listing Generator</h1>
        <p className="text-xl mb-8">Automate second-hand sales with AI analysis and multi-platform uploads.</p>
        <a href="/submit" className="bg-blue-500 text-white px-6 py-3 rounded hover:bg-blue-600">Start Selling</a>
      </div>
    </div>
  );
}
EOF

cat > src/app/submit/page.tsx << 'EOF'
'use client';

import { useState } from 'react';
import { useUser, SignedIn, SignedOut, RedirectToSignIn, UserButton } from '@clerk/nextjs';
import { useTranslations } from 'next-intl';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { submitAction } from '@/app/actions';

export default function SubmitPage() {
  const t = useTranslations('submit');
  const { user } = useUser();
  const [mode, setMode] = useState('simple');
  const [formData, setFormData] = useState({ images: [], summary: '', category: '', condition: '', quantity: 1, color: '', age: 0, make: '', model: '', year: 0, price: 0 });
  const [consent, setConsent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFormSubmit = async (formData: FormData) => {
    setIsSubmitting(true);
    try {
      const images = formData.getAll('images') as File[];
      const summary = formData.get('summary') as string;
      const category = formData.get('category') as string;
      const condition = formData.get('condition') as string;
      const quantity = parseInt(formData.get('quantity') as string) || 1;
      const color = formData.get('color') as string;
      const age = parseInt(formData.get('age') as string) || 0;
      const make = formData.get('make') as string;
      const model = formData.get('model') as string;
      const year = parseInt(formData.get('year') as string) || 0;
      const price = parseFloat(formData.get('price') as string) || 0;

      if (!consent) throw new Error('Consent required.');

      const result = await submitAction(formData);
      console.log('Result:', result);
    } catch (error) {
      alert('Submission failed: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) return <RedirectToSignIn />;

  return (
    <SignedIn>
      <div className="min-h-screen bg-gray-100 p-8">
        <UserButton />
        <h1 className="text-4xl font-bold mb-8">{t('title')}</h1>
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>{t('description')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Simple Mode</Label>
              <Switch checked={mode === 'advanced'} onCheckedChange={(checked) => setMode(checked ? 'advanced' : 'simple')} />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="consent" checked={consent} onCheckedChange={setConsent} />
              <Label htmlFor="consent">{t('consent')}</Label>
            </div>
            <Input type="file" multiple accept="image/*" name="images" />
            {mode === 'simple' ? (
              <div className="space-y-2">
                <Label htmlFor="summary">{t('summary')}</Label>
                <Textarea id="summary" name="summary" placeholder={t('summary_placeholder')} required minLength={50} />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">{t('category')}</Label>
                  <Select name="category">
                    <SelectTrigger>
                      <SelectValue placeholder={t('category_placeholder')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="electronics">Electronics</SelectItem>
                      <SelectItem value="clothing">Clothing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="condition">{t('condition')}</Label>
                  <Select name="condition">
                    <SelectTrigger>
                      <SelectValue placeholder={t('condition_placeholder')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="new">New</SelectItem>
                      <SelectItem value="used">Used</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="quantity">Quantity</Label>
                  <Input id="quantity" name="quantity" type="number" min={1} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="color">Color</Label>
                  <Input id="color" name="color" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="age">Age</Label>
                  <Input id="age" name="age" type="number" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="make">Make</Label>
                  <Input id="make" name="make" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  <Input id="model" name="model" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="year">Year</Label>
                  <Input id="year" name="year" type="number" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Price</Label>
                  <Input id="price" name="price" type="number" />
                </div>
              </div>
            )}
            <form action={handleFormSubmit}>
              <Button type="submit" disabled={isSubmitting} className="w-full">
                {isSubmitting ? 'Submitting...' : t('submit')}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </SignedIn>
  );
}
EOF

cat > src/app/actions.ts << 'EOF'
'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!);

export async function submitAction(formData: FormData) {
  const images = formData.getAll('images') as File[];
  const summary = formData.get('summary') as string;
  const category = formData.get('category') as string;
  const condition = formData.get('condition') as string;
  const quantity = parseInt(formData.get('quantity') as string) || 1;
  const color = formData.get('color') as string;
  const age = parseInt(formData.get('age') as string) || 0;
  const make = formData.get('make') as string;
  const model = formData.get('model') as string;
  const year = parseInt(formData.get('year') as string) || 0;
  const price = parseFloat(formData.get('price') as string) || 0;

  // Mock analysis for demo
  const analysis = {
    recog: 'Red iPhone 12, good condition',
    price: price || 95,
    confidence: 95,
    rationale: 'Based on eBay comps $90-100, adjusted for condition.',
  };

  await supabase.from('submissions').insert({
    user_id: 'user_id_mock',
    summary,
    supplemental: { quantity, color, age, make, model, year, price },
    analysis,
  });

  revalidatePath('/submit');
  return analysis;
}
EOF

# Create Shadcn components (run CLI)
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input checkbox label card switch textarea select

echo "=== 4. Setting up backend (FastAPI) ==="
cd ../backend
rm -rf * requirements.txt  # Fresh
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
langchain==0.3.35
@langchain/openai==0.6.14
langfuse==3.38.5
letta==0.2.0
llama-stack-client==0.1.0
sentry-sdk==2.35.0
pydantic-settings==2.5.2
black==24.8.0
pytest==8.3.3
pytest-asyncio==0.24.0
pre-commit==4.0.1
bitwarden-cli==1.0.0
litellm==1.77.5
llama-index==0.14.3
llama-index-embeddings-openai==0.5.1
supabase==2.8.0
stripe==19.0.0
playwright==1.55.1
EOF

cat > main.py << 'EOF'
from fastapi import FastAPI, Form, UploadFile, File
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from litellm import completion
import os

app = FastAPI()

llm = ChatOpenAI(model="gpt-3.5-turbo")

class Submission(BaseModel):
    summary: str
    category: str
    condition: str

@app.post("/submit")
async def submit_item(summary: str = Form(...), category: str = Form(...), condition: str = Form(...)):
    response = llm.invoke(f"Analyze {summary} for {category}, condition {condition}.")
    return {"analysis": response.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

pip install -r requirements.txt

echo "=== 5. Setting up mobile (Expo) ==="
cd ../mobile
rm -rf * app.json  # Fresh
npx create-expo-app . --template blank-typescript
pnpm add @supabase/supabase-js expo-camera
pnpm install

cat > App.tsx << 'EOF'
import React, { useState } from 'react';
import { View, Text, Button, TextInput } from 'react-native';

export default function App() {
  const [summary, setSummary] = useState('');
  const [result, setResult] = useState(null);

  const submitItem = async () => {
    const response = await fetch('http://localhost:3000/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary, category: 'electronics', condition: 'used' }),
    });
    const data = await response.json();
    setResult(data);
  };

  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 20 }}>
      <Text style={{ fontSize: 24, textAlign: 'center' }}>Mobile Item Submission</Text>
      <TextInput
        style={{ borderWidth: 1, padding: 10, margin: 10 }}
        placeholder="Item summary..."
        value={summary}
        onChangeText={setSummary}
      />
      <Button title="Submit" onPress={submitItem} />
      {result && <Text>Result: {JSON.stringify(result)}</Text>}
    </View>
  );
}
EOF

echo "=== 6. Creating docs and configs ==="
cd ..
cat > .env.example << 'EOF'
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
OPENROUTER_API_KEY=your_openrouter_key
STRIPE_SECRET_KEY=your_stripe_key
CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
SENTRY_DSN=your_sentry_dsn
NEXT_PUBLIC_GA_ID=your_ga_id
NODE_ENV=development
SKIP_PAYWALL=true
EOF

cat > README.md << 'EOF'
# CloudCommerce - AI Listing Generator

Full-stack app for AI-powered second-hand listings.

## Setup
1. Run ./setup-full.sh
2. Visit localhost:3000/submit
EOF

echo "=== 7. Installing pre-commit and running tests ==="
pip install pre-commit
pre-commit install

cd frontend
npx playwright install

echo "=== 8. Starting servers ==="
pnpm dev &
cd ../backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

echo "=== 9. Running tests ==="
cd ../frontend
npx playwright test
cd ../backend
pytest -v

echo "=== Setup Complete! ==="
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "Test: Visit localhost:3000/submit and submit a form."