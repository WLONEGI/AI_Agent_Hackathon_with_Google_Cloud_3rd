import { Sidebar } from "@/components/layout/Sidebar";

const phases = [
  { title: "プロット設計", description: "物語の骨組みを洗練させる段階です。" },
  { title: "キャラクター作成", description: "人物像や性格をビジュアルに落とし込みます。" },
  { title: "レイアウト", description: "ページごとのレイアウトを構築します。" },
  { title: "作画", description: "イラストを描き込み、ディテールを整えます。" },
  { title: "彩色", description: "色付けを行い、世界観を演出します。" },
  { title: "仕上げ", description: "効果やテキストを配置して完成へ近づけます。" },
  { title: "レビュー", description: "最終チェックを行い完成版を確認します。" },
];

export default function ProcessingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
      <Sidebar />

      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0a] via-[#111111] to-[#0f0f0f] opacity-60" />

      <div className="relative z-10 ml-16 flex flex-col min-h-screen">
        <header className="border-b border-white/10 px-8 py-6">
          <div className="flex flex-col gap-2">
            <span className="text-sm uppercase tracking-widest text-white/50">Processing View</span>
            <h1 className="text-3xl md:text-4xl font-semibold bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
              進行状況プレビュー
            </h1>
            <p className="text-sm text-white/60">
              ここではデザインのみを確認できます。リアルタイム処理やネットワーク通信は全て削除されています。
            </p>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-8 py-10">
          <div className="grid gap-6 xl:grid-cols-3">
            <section className="xl:col-span-2 space-y-6">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
                <h2 className="text-lg font-semibold text-white/80">ダイジェスト</h2>
                <p className="mt-3 text-sm text-white/60">
                  この領域にはチャットやステータス表示などの UI が配置されていました。現在はデザイン確認のためのスタティックコンテンツに置き換えています。
                </p>
                <div className="mt-6 space-y-4">
                  {["ユーザーからのメッセージ", "AI からの応答", "ステータス通知"].map((label) => (
                    <div key={label} className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3">
                      <p className="text-sm text-white/70">{label}</p>
                      <p className="mt-1 text-xs text-white/40">
                        実際のテキストやイベントの代わりに、UI プレースホルダーとして用意しています。
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <aside className="space-y-4">
              {phases.map((phase, index) => (
                <div
                  key={phase.title}
                  className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-xs text-white/50">フェーズ {index + 1}</p>
                      <h3 className="text-lg font-semibold text-white/80 mt-1">{phase.title}</h3>
                    </div>
                    <span className="material-symbols-outlined text-emerald-300">check_circle</span>
                  </div>
                  <p className="mt-3 text-sm text-white/60">{phase.description}</p>
                  <div className="mt-4 h-1.5 w-full rounded-full bg-white/10">
                    <div className="h-full w-full rounded-full bg-gradient-to-r from-blue-400 to-purple-400" />
                  </div>
                </div>
              ))}
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}
