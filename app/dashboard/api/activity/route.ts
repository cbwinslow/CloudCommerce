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

    // Get recent activity from submissions and sync jobs
    const { data: submissions } = await supabase
      .from('submissions')
      .select('id, created_at, analysis, listings')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(10);

    const { data: syncJobs } = await supabase
      .from('sync_jobs')
      .select('id, created_at, status, platform')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(10);

    const activities = [];

    // Process submissions
    if (submissions) {
      submissions.forEach(sub => {
        activities.push({
          id: `submission_${sub.id}`,
          type: 'listing',
          platform: 'AI Analysis',
          description: 'New item analyzed and listings generated',
          timestamp: sub.created_at,
          status: 'completed'
        });
      });
    }

    // Process sync jobs
    if (syncJobs) {
      syncJobs.forEach(job => {
        activities.push({
          id: `sync_${job.id}`,
          type: 'sync',
          platform: job.platform,
          description: `Account sync ${job.status}`,
          timestamp: job.created_at,
          status: job.status
        });
      });
    }

    // Sort by timestamp
    activities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    // Return most recent 10 activities
    return NextResponse.json(activities.slice(0, 10));

  } catch (error) {
    console.error('Error fetching recent activity:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
