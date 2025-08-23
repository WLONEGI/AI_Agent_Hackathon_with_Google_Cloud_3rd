import { useState, useEffect } from 'react'
import Head from 'next/head'

interface TaskResult {
  task_id: string
  status: string
  result?: any
}

export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')
  const [inputText, setInputText] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState<boolean>(false)
  const [currentTask, setCurrentTask] = useState<TaskResult | null>(null)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    checkAPIStatus()
  }, [])

  const checkAPIStatus = async () => {
    try {
      const response = await fetch('/api/health')
      const data = await response.json()
      setApiStatus(data.status)
    } catch {
      setApiStatus('error')
    }
  }

  const generateComic = async () => {
    if (!inputText.trim()) {
      alert('ストーリーテキストを入力してください')
      return
    }

    setIsGenerating(true)
    setResult(null)

    try {
      // Step 1: Start generation
      const response = await fetch('/api/comic/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_text: inputText
        })
      })

      if (!response.ok) {
        throw new Error('Generation failed')
      }

      const taskData = await response.json()
      setCurrentTask(taskData)

      // Step 2: Poll for results
      pollTaskStatus(taskData.task_id)

    } catch (error) {
      console.error('Generation failed:', error)
      alert('漫画生成に失敗しました')
      setIsGenerating(false)
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    const maxAttempts = 30 // 最大30回 (約30秒)
    let attempts = 0

    const poll = async () => {
      try {
        const response = await fetch(`/api/comic/result/${taskId}`)
        
        if (response.status === 202) {
          // Still processing
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(poll, 1000) // 1秒後にリトライ
          } else {
            setIsGenerating(false)
            alert('処理がタイムアウトしました')
          }
          return
        }

        if (response.ok) {
          const resultData = await response.json()
          setResult(resultData.result)
          setIsGenerating(false)
        } else {
          throw new Error('Failed to get result')
        }

      } catch (error) {
        console.error('Polling failed:', error)
        setIsGenerating(false)
        alert('結果の取得に失敗しました')
      }
    }

    poll()
  }

  return (
    <>
      <Head>
        <title>AI Comic Generator</title>
        <meta name="description" content="AI漫画生成サービス" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-purple-400 to-pink-400 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white p-8 rounded-lg shadow-lg">
            <h1 className="text-4xl font-bold text-gray-800 mb-2 text-center">
              🎨 AI Comic Generator
            </h1>
            <p className="text-center text-gray-600 mb-6">
              Phase 1-2: テキスト解析 → ストーリー構造化 | マルチエージェント処理
            </p>
            
            <div className="mb-6">
              <div className="bg-gray-100 p-4 rounded mb-4">
                <h2 className="text-lg font-semibold mb-2">システム状況</h2>
                <div className="flex justify-between items-center">
                  <span>API Status:</span>
                  <span className={`px-2 py-1 rounded ${
                    apiStatus === 'healthy' 
                      ? 'bg-green-200 text-green-800' 
                      : apiStatus === 'error'
                      ? 'bg-red-200 text-red-800'
                      : 'bg-yellow-200 text-yellow-800'
                  }`}>
                    {apiStatus}
                  </span>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ストーリーテキスト
                </label>
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="例: 勇敢な少年が魔法の森で冒険する物語..."
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  rows={4}
                  disabled={isGenerating}
                />
              </div>
              
              <button
                onClick={generateComic}
                disabled={isGenerating || !inputText.trim()}
                className={`w-full py-3 px-4 rounded-md font-bold ${
                  isGenerating || !inputText.trim()
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600'
                } text-white`}
              >
                {isGenerating ? '分析中...' : 'ストーリー分析を開始'}
              </button>
            </div>

            {/* Results Display */}
            {result && (
              <div className="bg-green-50 p-6 rounded-lg">
                <h2 className="text-xl font-bold text-green-800 mb-4">
                  ✅ 分析結果 ({result.total_phases_completed || 1} フェーズ完了)
                </h2>
                
                {/* Phase 1 Results */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-3">Phase 1: テキスト解析結果</h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded border">
                      <h4 className="font-semibold text-gray-800 mb-2">ジャンル分析</h4>
                      <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                        {JSON.stringify(result.phase1_result?.analysis_result?.genre_analysis || result.analysis_result?.genre_analysis, null, 2)}
                      </pre>
                    </div>
                    
                    <div className="bg-white p-4 rounded border">
                      <h4 className="font-semibold text-gray-800 mb-2">キャラクター</h4>
                      <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                        {JSON.stringify(result.phase1_result?.analysis_result?.characters || result.analysis_result?.characters, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>

                {/* Phase 2 Results */}
                {result.phase2_result && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-purple-800 mb-3">Phase 2: ストーリー構造化結果</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="bg-white p-4 rounded border">
                        <h4 className="font-semibold text-gray-800 mb-2">物語構造</h4>
                        <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(result.phase2_result.structure_result?.narrative_acts, null, 2)}
                        </pre>
                      </div>
                      
                      <div className="bg-white p-4 rounded border">
                        <h4 className="font-semibold text-gray-800 mb-2">プロットポイント</h4>
                        <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(result.phase2_result.structure_result?.plot_points, null, 2)}
                        </pre>
                      </div>
                      
                      <div className="bg-white p-4 rounded border">
                        <h4 className="font-semibold text-gray-800 mb-2">コンフリクト構造</h4>
                        <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(result.phase2_result.structure_result?.conflict_structure, null, 2)}
                        </pre>
                      </div>
                      
                      <div className="bg-white p-4 rounded border">
                        <h4 className="font-semibold text-gray-800 mb-2">マンガ最適化</h4>
                        <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(result.phase2_result.structure_result?.manga_optimizations, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-4 bg-blue-50 p-4 rounded">
                  <h3 className="font-semibold text-blue-800 mb-2">品質メトリクス</h3>
                  <div className="text-sm text-blue-700">
                    Phase 1総合スコア: {result.phase1_result?.quality_metrics?.overall_score?.toFixed(1) || result.quality_metrics?.overall_score?.toFixed(1)}点
                    {result.phase2_result && (
                      <> | Phase 2総合スコア: {result.phase2_result.quality_metrics?.overall_score?.toFixed(1)}点</>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            <div className="mt-6 text-center text-sm text-gray-500">
              🚀 Phase 1-2実装完了 | マルチエージェント AI パイプライン稼働中
            </div>
          </div>
        </div>
      </main>
    </>
  )
}