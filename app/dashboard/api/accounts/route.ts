import { NextRequest, NextResponse } from 'next/server';
import { currentUser } from '@clerk/nextjs/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

interface ConnectedAccount {
  id: string;
  platform: string;
  status: 'connected' | 'disconnected' | 'error';
  last_sync: string;
  items_count: number;
  error?: string;
  platform_id?: string;
  access_token?: string;
  refresh_token?: string;
  expires_at?: number;
}

export async function GET(req: NextRequest) {
  try {
    const user = await currentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get user's connected accounts
    const { data: accountsData } = await supabase
      .from('connected_accounts')
      .select('*')
      .eq('user_id', user.id);

    if (!accountsData) {
      return NextResponse.json([]);
    }

    // Process accounts data
    const accounts: ConnectedAccount[] = accountsData.map(account => {
      // Determine status based on various factors
      let status: 'connected' | 'disconnected' | 'error' = 'connected';
      let error: string | undefined;

      // Check if account is expired
      if (account.expires_at && account.expires_at < Date.now() / 1000) {
        status = 'error';
        error = 'Access token expired';
      }

      // Check if account has valid tokens
      if (!account.access_token) {
        status = 'disconnected';
        error = 'No access token';
      }

      // Get item count for this account
      const itemCount = account.items_count || 0;

      return {
        id: account.id,
        platform: account.platform,
        status,
        last_sync: account.last_sync || new Date().toISOString(),
        items_count: itemCount,
        error,
        platform_id: account.platform_id,
        access_token: account.access_token ? '***' : undefined,
        refresh_token: account.refresh_token ? '***' : undefined,
        expires_at: account.expires_at
      };
    });

    // Add mock accounts for platforms not yet connected
    const allPlatforms = ['ebay', 'amazon', 'mercari', 'facebook_marketplace', 'craigslist'];
    const connectedPlatforms = accounts.map(acc => acc.platform);
    
    for (const platform of allPlatforms) {
      if (!connectedPlatforms.includes(platform)) {
        accounts.push({
          id: `mock_${platform}`,
          platform,
          status: 'disconnected',
          last_sync: new Date().toISOString(),
          items_count: 0,
          error: 'Not connected'
        });
      }
    }

    return NextResponse.json(accounts);

  } catch (error) {
    console.error('Error fetching connected accounts:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const user = await currentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { platform, code, redirect_uri } = await req.json();

    if (!platform) {
      return NextResponse.json({ error: 'Platform is required' }, { status: 400 });
    }

    // Handle OAuth flow for different platforms
    let result;

    switch (platform) {
      case 'ebay':
        result = await handleEbayOAuth(user.id, code, redirect_uri);
        break;
      case 'amazon':
        result = await handleAmazonOAuth(user.id, code, redirect_uri);
        break;
      case 'mercari':
        result = await handleMercariOAuth(user.id, code, redirect_uri);
        break;
      case 'facebook_marketplace':
        result = await handleFacebookOAuth(user.id, code, redirect_uri);
        break;
      default:
        return NextResponse.json({ error: 'Unsupported platform' }, { status: 400 });
    }

    if (result.error) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    // Save account to database
    const { data: accountData, error: accountError } = await supabase
      .from('connected_accounts')
      .upsert({
        user_id: user.id,
        platform,
        platform_id: result.platform_id,
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        expires_at: result.expires_at,
        last_sync: new Date().toISOString(),
        items_count: 0,
        metadata: result.metadata || {}
      })
      .select()
      .single();

    if (accountError) {
      console.error('Error saving account:', accountError);
      return NextResponse.json({ error: 'Failed to save account' }, { status: 500 });
    }

    return NextResponse.json({
      success: true,
      account: {
        id: accountData.id,
        platform: accountData.platform,
        status: 'connected',
        last_sync: accountData.last_sync,
        items_count: 0
      }
    });

  } catch (error) {
    console.error('Error connecting account:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

async function handleEbayOAuth(userId: string, code: string, redirect_uri: string) {
  try {
    // eBay OAuth implementation
    const clientId = process.env.EBAY_CLIENT_ID;
    const clientSecret = process.env.EBAY_CLIENT_SECRET;
    
    if (!clientId || !clientSecret) {
      return { error: 'eBay credentials not configured' };
    }

    const tokenResponse = await fetch('https://api.ebay.com/identity/v1/oauth2/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: redirect_uri || process.env.EBAY_REDIRECT_URI,
        scope: 'https://api.ebay.com/oauth/api scope'
      })
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      return { error: tokenData.error_description || 'Failed to get eBay access token' };
    }

    // Get user's eBay user info
    const userResponse = await fetch('https://api.ebay.com/identity/v1/user', {
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`,
        'Content-Type': 'application/json'
      }
    });

    const userData = await userResponse.json();

    return {
      platform_id: userData.user_id,
      access_token: tokenData.access_token,
      refresh_token: tokenData.refresh_token,
      expires_at: Date.now() / 1000 + tokenData.expires_in,
      metadata: {
        username: userData.username,
        email: userData.email
      }
    };

  } catch (error) {
    console.error('eBay OAuth error:', error);
    return { error: 'Failed to connect eBay account' };
  }
}

async function handleAmazonOAuth(userId: string, code: string, redirect_uri: string) {
  try {
    // Amazon OAuth implementation
    const clientId = process.env.AMAZON_CLIENT_ID;
    const clientSecret = process.env.AMAZON_CLIENT_SECRET;
    
    if (!clientId || !clientSecret) {
      return { error: 'Amazon credentials not configured' };
    }

    const tokenResponse = await fetch('https://api.amazon.com/auth/o2/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirect_uri || process.env.AMAZON_REDIRECT_URI
      })
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      return { error: tokenData.error || 'Failed to get Amazon access token' };
    }

    // Get user's Amazon profile info
    const profileResponse = await fetch('https://api.amazon.com/user/profile', {
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`
      }
    });

    const profileData = await profileResponse.json();

    return {
      platform_id: profileData.user_id,
      access_token: tokenData.access_token,
      refresh_token: tokenData.refresh_token,
      expires_at: Date.now() / 1000 + tokenData.expires_in,
      metadata: {
        name: profileData.name,
        email: profileData.email
      }
    };

  } catch (error) {
    console.error('Amazon OAuth error:', error);
    return { error: 'Failed to connect Amazon account' };
  }
}

async function handleMercariOAuth(userId: string, code: string, redirect_uri: string) {
  try {
    // Mercari OAuth implementation
    const clientId = process.env.MERCARI_CLIENT_ID;
    const clientSecret = process.env.MERCARI_CLIENT_SECRET;
    
    if (!clientId || !clientSecret) {
      return { error: 'Mercari credentials not configured' };
    }

    const tokenResponse = await fetch('https://api.mercari.com/v1/oauth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: redirect_uri || process.env.MERCARI_REDIRECT_URI
      })
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      return { error: tokenData.error || 'Failed to get Mercari access token' };
    }

    return {
      platform_id: tokenData.user_id,
      access_token: tokenData.access_token,
      refresh_token: tokenData.refresh_token,
      expires_at: Date.now() / 1000 + tokenData.expires_in,
      metadata: {}
    };

  } catch (error) {
    console.error('Mercari OAuth error:', error);
    return { error: 'Failed to connect Mercari account' };
  }
}

async function handleFacebookOAuth(userId: string, code: string, redirect_uri: string) {
  try {
    // Facebook OAuth implementation
    const appId = process.env.FACEBOOK_APP_ID;
    const appSecret = process.env.FACEBOOK_APP_SECRET;
    
    if (!appId || !appSecret) {
      return { error: 'Facebook credentials not configured' };
    }

    const tokenResponse = await fetch('https://graph.facebook.com/v18.0/oauth/access_token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: redirect_uri || process.env.FACEBOOK_REDIRECT_URI,
        client_id: appId,
        client_secret: appSecret
      })
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      return { error: tokenData.error.message || 'Failed to get Facebook access token' };
    }

    // Get user's Facebook profile info
    const profileResponse = await fetch(`https://graph.facebook.com/v18.0/me?fields=id,name,email`, {
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`
      }
    });

    const profileData = await profileResponse.json();

    return {
      platform_id: profileData.id,
      access_token: tokenData.access_token,
      refresh_token: tokenData.refresh_token,
      expires_at: Date.now() / 1000 + tokenData.expires_in,
      metadata: {
        name: profileData.name,
        email: profileData.email
      }
    };

  } catch (error) {
    console.error('Facebook OAuth error:', error);
    return { error: 'Failed to connect Facebook account' };
  }
}