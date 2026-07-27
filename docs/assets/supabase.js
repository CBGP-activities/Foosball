const SUPABASE_URL = "https://ymwrdrnyckixvdozrzhr.supabase.co";

const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inltd3Jkcm55Y2tpeHZkb3pyemhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUxMzYzOTAsImV4cCI6MjEwMDcxMjM5MH0.HoJzcwmzrGHyRhM1h-jwFQ1LJD9eaaHQs41vQD93ehY";


const supabaseClient = supabase.createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);
