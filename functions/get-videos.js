import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from 'jsr:@supabase/supabase-js@2';
Deno.serve(async (req)=>{
  try {
    const url = new URL(req.url);
    // 🗝 Get API key from query or headers
    const apiKey = url.searchParams.get('x-api-key') || req.headers.get('x-api-key');
    if (!apiKey) {
      return new Response(JSON.stringify({
        message: 'Missing API key'
      }), {
        status: 401
      });
    }
    // 🔢 Parse pagination parameters
    const perPage = 5;
    const lastId = Number(url.searchParams.get('last_id') ?? 0);
    const host = url.searchParams.get('host') || req.headers.get('host');
    if (!host) {
      return new Response(JSON.stringify({
        message: 'Missing host'
      }), {
        status: 400
      });
    }
    const supabase = createClient(Deno.env.get('SUPABASE_URL') ?? '', Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '');
    // ✅ Validate API key
    const { data: apiKeyRow, error: apiKeyError } = await supabase.from('api_keys').select('*').eq('api_key', apiKey).eq('enabled', true).gte('expire_at', new Date().toISOString()).maybeSingle();
    if (apiKeyError || !apiKeyRow) {
      return new Response(JSON.stringify({
        message: 'Invalid or expired API key'
      }), {
        status: 403
      });
    }
    if (!apiKeyRow.hosts.includes(host)) {
      return new Response(JSON.stringify({
        message: 'Host not allowed'
      }), {
        status: 403
      });
    }
    // 📺 Query videos
    const { data: videos, error: videoError } = await supabase.from('videos').select('*').gt('id', lastId).eq('status', 'published').order('id', {
      ascending: true
    }).limit(perPage);
    if (videoError) throw videoError;
    return new Response(JSON.stringify(videos), {
      headers: {
        'Content-Type': 'application/json'
      },
      status: 200
    });
  } catch (err) {
    return new Response(JSON.stringify({
      message: err?.message ?? err
    }), {
      headers: {
        'Content-Type': 'application/json'
      },
      status: 500
    });
  }
});
