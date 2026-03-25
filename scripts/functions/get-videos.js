import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient} from 'jsr:@supabase/supabase-js@2';

// Helper functions
const createErrorResponse = (message, status = 400) => {
    return new Response(JSON.stringify({message}), {
        headers: {'Content-Type': 'application/json'},
        status
    });
};

const createSuccessResponse = (data) => {
    return new Response(JSON.stringify(data), {
        headers: {'Content-Type': 'application/json'},
        status: 200
    });
};

const processVideoUrls = (video) => {
    return {
        ...video,
        tag_translations: {},
        category_translations: {},
    };
};

const collectTerms = (videos) => {
    const allTerms = new Set();
    videos.forEach(video => {
        if (video.tags) video.tags.forEach(tag => allTerms.add(tag.toLowerCase()));
        if (video.keyword) {
            if (!video.categories) video.categories = [];
            video.categories.push(video.keyword.toLowerCase());
        }
        if (video.categories) video.categories.forEach(cat => allTerms.add(cat.toLowerCase()));
    });
    return allTerms;
};

const createTranslationMap = (translations) => {
    const translationMap = new Map();
    translations.forEach(t => {
        const lowerText = t.text.toLowerCase();
        if (!translationMap.has(lowerText)) {
            translationMap.set(lowerText, []);
        }
        translationMap.get(lowerText).push(t);
    });
    return translationMap;
};

const processTranslations = (video, translationMap) => {
    const tagTranslations = {};
    const categoryTranslations = {};

    if (video.tags) {
        video.tags.forEach(tag => {
            const tagTrans = translationMap.get(tag.toLowerCase()) || [];
            tagTrans.forEach(t => {
                if (!tagTranslations[t.lang]) {
                    tagTranslations[t.lang] = [];
                }
                tagTranslations[t.lang].push(t.translation);
            });
        });
    }

    if (video.categories) {
        video.categories.forEach(cat => {
            const catTrans = translationMap.get(cat.toLowerCase()) || [];
            catTrans.forEach(t => {
                if (!categoryTranslations[t.lang]) {
                    categoryTranslations[t.lang] = [];
                }
                categoryTranslations[t.lang].push(t.translation);
            });
        });
    }

    return {tagTranslations, categoryTranslations};
};

Deno.serve(async (req) => {
    try {
        const url = new URL(req.url);
        const apiKey = url.searchParams.get('x-api-key') || req.headers.get('x-api-key');
        if (!apiKey) {
            return createErrorResponse('Missing API key', 401);
        }

        const perPage = 5;
        const lastIdStr = url.searchParams.get('last_id');
        if (!lastIdStr) {
            return createErrorResponse('Missing last_id', 400);
        }
        const lastId = Number(lastIdStr);

        const host = url.searchParams.get('host');
        if (!host) {
            return createErrorResponse('Missing host', 400);
        }

        const supabase = createClient(Deno.env.get('SUPABASE_URL') ?? '', Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '');

        // Validate API key
        const {data: apiKeyRow, error: apiKeyError} = await supabase
            .from('api_keys')
            .select('*')
            .eq('api_key', apiKey)
            .eq('enabled', true)
            .gte('expire_at', new Date().toISOString())
            .maybeSingle();

        if (apiKeyError || !apiKeyRow) {
            return createErrorResponse('Invalid or expired API key', 403);
        }

        const normalizedHost = host.replace(/^www\./, '');
        if (apiKeyRow.host !== normalizedHost) {
            return createErrorResponse('Host not allowed', 403);
        }

        // Get videos
        const {data: videos, error: videoError} = await supabase
            .from('videos')
            .select("id, host, title, url, filename, keyword, title_translations, file_size, duration, width, height, aspect_ratio, tags, categories, thumbnail_url")
            .gt('id', lastId)
            .eq('status', 'published')
            .order('id', {ascending: true})
            .limit(perPage);

        if (videoError) throw videoError;

        // Process videos with URLs
        const processedVideos = videos.map(processVideoUrls);

        // Get all terms for translation
        const allTerms = collectTerms(videos);
        if (allTerms.size === 0) {
            return createSuccessResponse(processedVideos);
        }

        // Get translations
        const {data: translations, error: translationError} = await supabase
            .from('terms')
            .select('id, text, lang, translation')
            .in('text', Array.from(allTerms));

        if (translationError) throw translationError;

        // Process translations
        const translationMap = createTranslationMap(translations);
        const videosWithTranslations = processedVideos.map((video, index) => {
            const {tagTranslations, categoryTranslations} = processTranslations(videos[index], translationMap);
            return {
                ...video,
                tag_translations: tagTranslations,
                category_translations: categoryTranslations
            };
        });

        return createSuccessResponse(videosWithTranslations);
    } catch (err) {
        console.error('Error:', err);
        return createErrorResponse(err?.message ?? 'Internal server error', 500);
    }
});
