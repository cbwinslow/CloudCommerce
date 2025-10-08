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

    // Get category distribution from submissions
    const { data: submissions } = await supabase
      .from('submissions')
      .select('analysis')
      .eq('user_id', user.id);

    // Mock category distribution data
    const categories = [
      { category: 'Electronics', count: Math.floor(Math.random() * 50) + 10, value: Math.floor(Math.random() * 5000) + 1000 },
      { category: 'Clothing', count: Math.floor(Math.random() * 40) + 5, value: Math.floor(Math.random() * 3000) + 500 },
      { category: 'Home & Garden', count: Math.floor(Math.random() * 30) + 5, value: Math.floor(Math.random() * 4000) + 800 },
      { category: 'Collectibles', count: Math.floor(Math.random() * 20) + 3, value: Math.floor(Math.random() * 8000) + 2000 },
      { category: 'Books', count: Math.floor(Math.random() * 25) + 2, value: Math.floor(Math.random() * 1000) + 200 },
      { category: 'Other', count: Math.floor(Math.random() * 15) + 1, value: Math.floor(Math.random() * 2000) + 300 }
    ];

    return NextResponse.json(categories);

  } catch (error) {
    console.error('Error fetching category distribution:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
