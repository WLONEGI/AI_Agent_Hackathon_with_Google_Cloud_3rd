import Image from "next/image";

export function Sidebar() {
  return (
    <div className="fixed left-0 top-0 h-full w-16 bg-gradient-to-b from-gray-900/95 to-black/95 backdrop-blur-xl border-r border-white/10 z-50 shadow-2xl">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-r-2xl" />
      <div className="relative flex flex-col h-full">
        <div className="flex items-center justify-center h-16 border-b border-white/10">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-full blur-lg" />
            <Image
              src="/logo.svg"
              alt="Spell"
              width={24}
              height={24}
              className="relative rounded-full"
            />
          </div>
        </div>

        <nav className="flex-1 py-6">
          <div className="space-y-1 px-3">
            <span className="relative group block w-full px-2 py-2 rounded-xl text-gray-300 hover:text-white transition-colors duration-300">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative flex items-center justify-center">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
            </span>

            <span className="relative group block w-full px-2 py-2 rounded-xl text-gray-300 hover:text-white transition-colors duration-300">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative flex items-center justify-center">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </span>
          </div>
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className="relative group block w-full px-2 py-2 rounded-xl text-gray-300 hover:text-white transition-colors duration-300">
            <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-pink-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative flex items-center justify-center">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
