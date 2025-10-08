import { NextRequest, NextResponse } from 'next/server';
import { currentUser } from '@clerk/nextjs/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

export async function GET(req: NextRequest) {
  try {
    const user = await currentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get user's dashboard statistics
    const { data: userData } = await supabase
      .from('users')
      .select('credits, sub_status')
      .eq('id', user.id)
      .single();

    // Get total items count
    const { count: totalItems } = await supabase
      .from('crawled_items')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id);

    // Get total value of items
    const { data: valueData } = await supabase
      .from('crawled_items')
      .select('price')
      .eq('user_id', user.id);

    const totalValue = valueData?.reduce((sum, item) => sum + (item.price || 0), 0) || 0;

    // Get average quality score
    const { data: qualityData } = await supabase
      .from('crawled_items')
      .select('quality_score')
      .eq('user_id', user.id);

    const avgQualityScore = qualityData && qualityData.length > 0
      ? qualityData.reduce((sum, item) => sum + (item.quality_score || 0), 0) / qualityData.length
      : 0;

    // Get active listings count
    const { count: activeListings } = await supabase
      .from('listings')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .eq('status', 'active');

    // Get pending sync count
    const { count: pendingSync } = await supabase
      .from('sync_jobs')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .eq('status', 'pending');

    // Get arbitrage opportunities
    const { data: arbitrageData } = await supabase
      .from('crawled_items')
      .select('arbitrage_potential')
      .eq('user_id', user.id)
      .gt('arbitrage_potential', 0);

    const arbitrageOpportunities = arbitrageData?.length || 0;

    return NextResponse.json({
      total_items: totalItems || 0,
      total_value: totalValue,
      avg_quality_score: parseFloat(avgQualityScore.toFixed(2)),
      active_listings: activeListings || 0,
      pending_sync: pendingSync || 0,
      arbitrage_opportunities: arbitrageOpportunities,
      user_credits: userData?.credits || 0,
      subscription_status: userData?.sub_status || 'free'
    });

  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}