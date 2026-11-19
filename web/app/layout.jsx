export const metadata = { title: "MusicProfiler", description: "Private Spotify collector status" };
export default function RootLayout({ children }) {
  return <html lang="en"><body style={{fontFamily:"system-ui,sans-serif",margin:"2rem auto",maxWidth:850,padding:"0 1rem",background:"#101417",color:"#e8edf0"}}>{children}</body></html>;
}
