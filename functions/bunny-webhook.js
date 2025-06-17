import {createClient} from 'https://esm.sh/@supabase/supabase-js@2';

Deno.serve(async (req) => {
    const {VideoGuid, Status} = await req.json();
    console.log(VideoGuid, Status);
    if (Status === 3) {
        const supabase = createClient(Deno.env.get('SUPABASE_URL'), Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'));
        await supabase.from('videos').update({
            status: 'published',
            updated_at: new Date().toISOString()
        }).eq('bunny_video_id', VideoGuid);
    }
    return new Response('OK');
});
