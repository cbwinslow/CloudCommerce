import { NextRequest, NextResponse } from 'next/server';
import { currentUser } from '@clerk/nextjs/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!);

export async function GET(req: NextRequest) {
  try {
    const user = await currentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Generate mock price trends data for the last 30 days
    const trends = [];
    const today = new Date();
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      // Generate realistic price trend data
      const basePrice = 150 + Math.sin(i * 0.3) * 30 + Math.random() * 20;
      
      trends.push({
        date: date.toISOString().split('T')[0],
        price: Math.round(basePrice),
        platform: 'Average'
      });
    }

    return NextResponse.json(trends);

  } catch (error) {
    console.error('Error fetching price trends:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
