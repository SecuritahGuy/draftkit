export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 text-neutral-900">
      <header className="border-b border-neutral-300 bg-white/95 backdrop-blur-sm shadow-lg">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent">
            DraftKit
          </h1>
          <p className="mt-2 text-sm text-neutral-600 font-medium">
            2025 projections • 2024/2023/2022 blend (60%/30%/10%)
          </p>
        </div>
      </header>
      <main className="mx-auto grid max-w-7xl grid-cols-12 gap-8 px-6 py-8">
        {children}
      </main>
    </div>
  );
}
