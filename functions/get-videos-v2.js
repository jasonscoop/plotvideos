import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient} from 'jsr:@supabase/supabase-js@2';

const CDN_DOMAIN = Deno.env.get('CDN_DOMAIN') ?? 'https://play.luckvideos.com';

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


const buildVideoHtml = (storeDir, filename, availableLangs, languageMap) => {
    const mp4Url = `${CDN_DOMAIN}/${storeDir}/${filename}`;
    
    const tracksHtml = [];
    for (const lang of availableLangs) {
        const trackUrl = `${CDN_DOMAIN}/${storeDir}/subtitles/${lang}.vtt`;
        const nativeName = languageMap.get(lang) || lang;
        tracksHtml.push(
            `<track kind="subtitles" src="${trackUrl}" srclang="${lang}" label="${nativeName}">`
        );
    }
    
    return `<video controls src="${mp4Url}" preload="metadata" crossorigin="anonymous">
    ${tracksHtml.join('\n    ')}
    Your browser does not support the video tag.</video>`;
};

const processVideoUrls = async (video, termTranslationMap, languageMap) => {
    const {store_dir, filename, ...videoWithoutSensitive} = video;

    // Parse title translations
    let titleTranslations = {};
    if (video.title_translations) {
        try {
            const translations = typeof video.title_translations === 'string' 
                ? JSON.parse(video.title_translations) 
                : video.title_translations;
            
            if (Array.isArray(translations)) {
                // Handle array of objects
                translations.forEach(item => {
                    if (typeof item === 'object' && item !== null) {
                        Object.assign(titleTranslations, item);
                    }
                });
            } else if (typeof translations === 'object') {
                titleTranslations = translations;
            }
        } catch (e) {
            console.error('Error parsing title_translations:', e);
        }
    }

    // Get available languages from title translations
    const availableLangs = Object.keys(titleTranslations);

    // Generate metas for each language that has a title translation
    const metas = [];
    for (const langCode of availableLangs) {
        const meta = {
            lang: langCode,
            title: titleTranslations[langCode],
            tags: [],
            categories: []
        };

        // Add translated tags
        if (video.tags) {
            video.tags.forEach(tag => {
                const tagTrans = termTranslationMap.get(tag.toLowerCase()) || [];
                const langTranslation = tagTrans.find(t => t.lang === langCode);
                if (langTranslation) {
                    meta.tags.push(langTranslation.translation);
                }
            });
        }

        // Add translated categories (including keyword)
        const categories = [...(video.categories || [])];
        if (video.keyword) {
            categories.push(video.keyword.toLowerCase());
        }
        
        categories.forEach(cat => {
            const catTrans = termTranslationMap.get(cat.toLowerCase()) || [];
            const langTranslation = catTrans.find(t => t.lang === langCode);
            if (langTranslation) {
                meta.categories.push(langTranslation.translation);
            }
        });

        metas.push(meta);
    }

    return {
        id: video.id,
        title: video.title,
        file_size: video.file_size,
        duration: video.duration,
        width: video.width,
        height: video.height,
        aspect_ratio: video.aspect_ratio,
        metas: metas,
        html_content: buildVideoHtml(store_dir, filename, availableLangs, languageMap),
        thumbnail_url: `${CDN_DOMAIN}/${store_dir}/thumbnail.webp`
    };
};

const collectTerms = (videos) => {
    const allTerms = new Set();
    videos.forEach(video => {
        if (video.tags) {
            video.tags.forEach(tag => allTerms.add(tag.toLowerCase()));
        }
        if (video.keyword) {
            allTerms.add(video.keyword.toLowerCase());
        }
        if (video.categories) {
            video.categories.forEach(cat => allTerms.add(cat.toLowerCase()));
        }
    });
    return allTerms;
};

const createTermTranslationMap = (translations) => {
    const map = new Map();
    translations.forEach(t => {
        const lowerText = t.text.toLowerCase();
        if (!map.has(lowerText)) {
            map.set(lowerText, []);
        }
        map.get(lowerText).push(t);
    });
    return map;
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

        // Get videos with only the required columns
        const {data: videos, error: videoError} = await supabase
            .from('videos')
            .select("id, title, keyword, file_size, duration, width, height, aspect_ratio, title_translations, tags, categories, store_dir, filename")
            .gt('id', lastId)
            .eq('status', 'published')
            .order('id', {ascending: true})
            .limit(perPage);

        if (videoError) throw videoError;
        if (videos.length === 0) {
            return createSuccessResponse([]);
        }

        // Get all terms for translation
        const allTerms = collectTerms(videos);
        
        // Get translations
        let translationMap = new Map();
        if (allTerms.size > 0) {
            const {data: translations, error: translationError} = await supabase
                .from('terms')
                .select('id, text, lang, translation')
                .in('text', Array.from(allTerms));

            if (translationError) throw translationError;
            translationMap = createTermTranslationMap(translations);
        }

        // Get all languages and create a map
        const {data: languages, error: languageError} = await supabase
        .from('languages')
        .select('code, native_name');
    
        if (languageError) throw languageError;

        const languageMap = new Map();
        languages.forEach(lang => {
            languageMap.set(lang.code, lang.native_name);
        });

        // Process videos with optimized structure
        const processedVideos = await Promise.all(
            videos.map(video => processVideoUrls(video, translationMap, languageMap))
        );

        return createSuccessResponse(processedVideos);
    } catch (err) {
        console.error('Error:', err);
        return createErrorResponse(err?.message ?? 'Internal server error', 500);
    }
});
