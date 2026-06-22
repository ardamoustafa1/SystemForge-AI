export default function RootLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-white/5 bg-background/95 p-4">
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <div className="h-8 w-32 animate-pulse rounded-md bg-white/5" />
          <div className="flex gap-4">
            <div className="h-8 w-8 animate-pulse rounded-full bg-white/5" />
            <div className="h-8 w-8 animate-pulse rounded-full bg-white/5" />
          </div>
        </div>
      </div>
      <div className="mx-auto max-w-7xl p-8">
        <div className="h-10 w-48 animate-pulse rounded-lg bg-white/5 mb-8" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-white/5 bg-white/[0.02]" />
          ))}
        </div>
      </div>
    </div>
  );
}
