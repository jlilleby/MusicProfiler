export const dynamic = "force-dynamic";
async function getStatus() {
  try {
    const response = await fetch((process.env.BACKEND_URL || "http://api:8000") + "/api/status", {cache:"no-store"});
    if (!response.ok) throw Error("API unavailable");
    return await response.json();
  } catch { return null; }
}
export default async function Home() {
  const status = await getStatus();
  return <main>
    <h1>MusicProfiler</h1>
    <p style={{color:"#9bb0b8"}}>Self-hosted Spotify API collector — operational status</p>
    <section style={{padding:20,background:"#1d252a",borderRadius:12}}>
      <h2>Connection</h2>
      <p>{status ? (status.connected ? "Spotify connected" : "Spotify not connected") : "Backend unavailable"}</p>
      <p>Recently played: {status?.recent_poll_seconds ?? "—"} seconds</p>
      <p>Current playback: {status?.playback_poll_seconds ?? "—"} seconds</p>
    </section>
    <h2>Collector jobs</h2>
    {status?.jobs?.length ? <ul>{status.jobs.map(job =>
      <li key={job.job_name} style={{marginBottom:16}}><strong>{job.job_name}</strong>: {job.last_message || "no result"}
      <div style={{color:"#9bb0b8"}}>Last success: {job.last_success_at || "never"} · HTTP: {job.last_http_status ?? "—"}</div></li>
    )}</ul> : <p>No collector activity recorded yet.</p>}
    <p style={{color:"#9bb0b8"}}>This dashboard does not store or analyze Spotify listening history.</p>
  </main>;
}
