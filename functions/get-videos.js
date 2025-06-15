import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from 'jsr:@supabase/supabase-js@2';

Deno.serve(async (req) => {
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
    const host = url.searchParams.get('host');
    if (!host) {
      return new Response(JSON.stringify({
        message: 'Missing host'
      }), {
        status: 400
      });
    }

    const supabase = createClient(Deno.env.get('SUPABASE_URL') ?? '', Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '');

    // ✅ Validate API key
    const { data: apiKeyRow, error: apiKeyError } = await supabase
      .from('api_keys')
      .select('*')
      .eq('api_key', apiKey)
      .eq('enabled', true)
      .gte('expire_at', new Date().toISOString())
      .maybeSingle();

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
    const { data: videos, error: videoError } = await supabase
      .from('videos')
      .select('*')
      .gt('id', lastId)
      .eq('status', 'published')
      .order('id', { ascending: true })
      .limit(perPage);

    if (videoError) throw videoError;

    // Get all unique tags and categories from videos
    const allTerms = new Set();
    videos.forEach(video => {
      video.tags.forEach(tag => allTerms.add(tag));
      video.categories.forEach(cat => allTerms.add(cat));
    });

    if (allTerms.size > 0) {
      // Get translations for all terms in a single query
      const { data: translations, error: translationError } = await supabase
        .from('terms')
        .select('id, text, lang, translation')
        .in('text', Array.from(allTerms));

      if (translationError) throw translationError;

      // Create a map for faster lookups
      const translationMap = new Map();
      translations.forEach(t => {
        if (!translationMap.has(t.text)) {
          translationMap.set(t.text, []);
        }
        translationMap.get(t.text).push(t);
      });

      // Process videos to add translations
      const processedVideos = videos.map(video => {
        const tagTranslations = [];
        const categoryTranslations = [];

        // Get translations for tags
        video.tags.forEach(tag => {
          const tagTrans = translationMap.get(tag) || [];
          tagTranslations.push(...tagTrans);
        });

        // Get translations for categories
        video.categories.forEach(cat => {
          const catTrans = translationMap.get(cat) || [];
          categoryTranslations.push(...catTrans);
        });

        return {
          ...video,
          tag_translations: tagTranslations,
          category_translations: categoryTranslations
        };
      });

      return new Response(JSON.stringify(processedVideos), {
        headers: {
          'Content-Type': 'application/json'
        },
        status: 200
      });
    }

    // If no terms found, return videos without translations
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
