import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient} from 'jsr:@supabase/supabase-js@2';
// Helper functions
const createErrorResponse = (message, status = 400) => {
    return new Response(JSON.stringify({
        message
    }), {
        headers: {
            'Content-Type': 'application/json'
        },
        status
    });
};
const createSuccessResponse = (data) => {
    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json'
        },
        status: 200
    });
};
Deno.serve(async (req) => {
    try {
        const url = new URL(req.url);
        const apiKey = url.searchParams.get('x-api-key') || req.headers.get('x-api-key');
        if (!apiKey) {
            return createErrorResponse('Missing API key', 401);
        }
        const host = url.searchParams.get('host');
        if (!host) {
            return createErrorResponse('Missing host', 400);
        }
        const supabase = createClient(Deno.env.get('SUPABASE_URL') ?? '', Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '');
        // Validate API key
        const {
            data: apiKeyRow,
            error: apiKeyError
        } = await supabase.from('api_keys').select('*').eq('api_key', apiKey).eq('enabled', true).gte('expire_at', new Date().toISOString()).maybeSingle();
        if (apiKeyError || !apiKeyRow) {
            return createErrorResponse('Invalid or expired API key', 403);
        }
        if (!apiKeyRow.hosts.includes(host)) {
            return createErrorResponse('Host not allowed', 403);
        }
        // Get videos
        const {
            data: languages,
            error: videoError
        } = await supabase.from('languages').select("id, code, locale, native_name").eq('enabled', true).order('id', {
            ascending: true
        });
        if (videoError) throw videoError;
        return createSuccessResponse(languages);
    } catch (err) {
        console.error('Error:', err);
        return createErrorResponse(err?.message ?? 'Internal server error', 500);
    }
});
