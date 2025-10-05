import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: 'https://openrouter.ai/api/v1',
});

export { openai as openrouter };

export async function analyzeWithOpenRouter(prompt: string, model = 'llava-13b-v1.6') {
  const response = await openai.chat.completions.create({
    model,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 500,
  });
  return response.choices[0].message.content;
}

export async function analyzeItem(images: string[], summary: string, category?: string, condition?: string) {
  // Low-cost model for vision: LLaVA or GPT-4o-mini
  const prompt = `Analyze these images and summary: "${summary}". Category: ${category || 'unknown'}. Condition: ${condition || 'unknown'}.
  Extract: name, description, price range, condition details, damage, age, industry, usage. Use scraped data if available.`;

  const response = await openai.chat.completions.create({
    model: 'llava-13b-v1.6', // Free/low-cost vision model on OpenRouter
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          ...images.map((img) => ({
            type: 'image_url' as const,
            image_url: { url: img }
          })),
        ],
      },
    ],
    max_tokens: 500,
  });

  return response.choices[0].message.content;
}

export async function generateListings(analysis: string, platforms: string[]) {
  const prompt = `Based on analysis: ${analysis}. Generate listings for ${platforms.join(', ')} (title, desc, price, condition). Format as JSON.`;

  const response = await openai.chat.completions.create({
    model: 'meta-llama/llama-3.1-8b-instruct:free', // Free tier model
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 1000,
  });

  return JSON.parse(response.choices[0].message.content || '{}');
}
