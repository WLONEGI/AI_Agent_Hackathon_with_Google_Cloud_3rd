'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  GitBranch,
  GitCommit,
  GitMerge,
  GitPullRequest,
  Clock,
  User,
  Tag,
  ChevronRight,
  Save,
  RotateCcw,
  Copy,
  Trash2,
  Check
} from 'lucide-react';
import { type PhaseId } from '@/types/processing';

interface Version {
  id: string;
  name: string;
  description: string;
  timestamp: Date;
  author: string;
  phaseId: PhaseId;
  data: any;
  parent?: string;
  branch: string;
  tags?: string[];
}

interface Branch {
  name: string;
  baseVersion: string;
  versions: string[];
  isActive: boolean;
  createdAt: Date;
}

interface VersionManagerProps {
  currentData: any;
  currentPhaseId: PhaseId;
  onRestore: (version: Version) => void;
  onMerge?: (sourceVersion: Version, targetVersion: Version) => void;
}

export function VersionManager({ 
  currentData, 
  currentPhaseId, 
  onRestore,
  onMerge 
}: VersionManagerProps) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [branches, setBranches] = useState<Branch[]>([
    {
      name: 'main',
      baseVersion: '',
      versions: [],
      isActive: true,
      createdAt: new Date()
    }
  ]);
  const [currentBranch, setCurrentBranch] = useState('main');
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [showNewVersionDialog, setShowNewVersionDialog] = useState(false);
  const [versionName, setVersionName] = useState('');
  const [versionDescription, setVersionDescription] = useState('');
  const [showNewBranchDialog, setShowNewBranchDialog] = useState(false);
  const [branchName, setBranchName] = useState('');
  const [compareMode, setCompareMode] = useState(false);
  const [compareVersions, setCompareVersions] = useState<[string | null, string | null]>([null, null]);

  // ローカルストレージから履歴を読み込み
  useEffect(() => {
    const storedVersions = localStorage.getItem('manga-versions');
    const storedBranches = localStorage.getItem('manga-branches');
    
    if (storedVersions) {
      const parsed = JSON.parse(storedVersions);
      setVersions(parsed.map((v: any) => ({
        ...v,
        timestamp: new Date(v.timestamp)
      })));
    }
    
    if (storedBranches) {
      const parsed = JSON.parse(storedBranches);
      setBranches(parsed.map((b: any) => ({
        ...b,
        createdAt: new Date(b.createdAt)
      })));
    }
  }, []);

  // 履歴を保存
  const saveToStorage = () => {
    localStorage.setItem('manga-versions', JSON.stringify(versions));
    localStorage.setItem('manga-branches', JSON.stringify(branches));
  };

  // 新しいバージョンを作成
  const createVersion = () => {
    if (!versionName) return;

    const newVersion: Version = {
      id: `v-${Date.now()}`,
      name: versionName,
      description: versionDescription,
      timestamp: new Date(),
      author: 'Current User', // 実際の実装では認証情報から取得
      phaseId: currentPhaseId,
      data: currentData,
      parent: versions.filter(v => v.branch === currentBranch).slice(-1)[0]?.id,
      branch: currentBranch,
      tags: []
    };

    const updatedVersions = [...versions, newVersion];
    setVersions(updatedVersions);

    // ブランチのバージョンリストを更新
    const updatedBranches = branches.map(b => 
      b.name === currentBranch 
        ? { ...b, versions: [...b.versions, newVersion.id] }
        : b
    );
    setBranches(updatedBranches);

    // ストレージに保存
    localStorage.setItem('manga-versions', JSON.stringify(updatedVersions));
    localStorage.setItem('manga-branches', JSON.stringify(updatedBranches));

    // ダイアログを閉じる
    setShowNewVersionDialog(false);
    setVersionName('');
    setVersionDescription('');
  };

  // 新しいブランチを作成
  const createBranch = () => {
    if (!branchName || branches.some(b => b.name === branchName)) return;

    const baseVersion = selectedVersion || versions.filter(v => v.branch === currentBranch).slice(-1)[0]?.id || '';
    
    const newBranch: Branch = {
      name: branchName,
      baseVersion,
      versions: [],
      isActive: false,
      createdAt: new Date()
    };

    const updatedBranches = [...branches, newBranch];
    setBranches(updatedBranches);
    localStorage.setItem('manga-branches', JSON.stringify(updatedBranches));

    setShowNewBranchDialog(false);
    setBranchName('');
  };

  // ブランチを切り替え
  const switchBranch = (branchName: string) => {
    setCurrentBranch(branchName);
    const updatedBranches = branches.map(b => ({
      ...b,
      isActive: b.name === branchName
    }));
    setBranches(updatedBranches);
    localStorage.setItem('manga-branches', JSON.stringify(updatedBranches));
  };

  // バージョンを復元
  const handleRestore = (versionId: string) => {
    const version = versions.find(v => v.id === versionId);
    if (version) {
      onRestore(version);
    }
  };

  // バージョンを削除
  const deleteVersion = (versionId: string) => {
    const updatedVersions = versions.filter(v => v.id !== versionId);
    setVersions(updatedVersions);
    
    const updatedBranches = branches.map(b => ({
      ...b,
      versions: b.versions.filter(id => id !== versionId)
    }));
    setBranches(updatedBranches);
    
    localStorage.setItem('manga-versions', JSON.stringify(updatedVersions));
    localStorage.setItem('manga-branches', JSON.stringify(updatedBranches));
  };

  // バージョンを比較
  const handleCompare = () => {
    if (compareVersions[0] && compareVersions[1]) {
      const v1 = versions.find(v => v.id === compareVersions[0]);
      const v2 = versions.find(v => v.id === compareVersions[1]);
      
      if (v1 && v2 && onMerge) {
        onMerge(v1, v2);
      }
    }
  };

  // タグを追加
  const addTag = (versionId: string, tag: string) => {
    const updatedVersions = versions.map(v => 
      v.id === versionId 
        ? { ...v, tags: [...(v.tags || []), tag] }
        : v
    );
    setVersions(updatedVersions);
    localStorage.setItem('manga-versions', JSON.stringify(updatedVersions));
  };

  // 現在のブランチのバージョンを取得
  const branchVersions = versions.filter(v => v.branch === currentBranch);

  return (
    <Card className="h-full flex flex-col bg-[rgb(var(--bg-secondary))] border-[rgb(var(--border-default))]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-[rgb(var(--accent-primary))]" />
            <CardTitle className="text-base">バージョン管理</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {currentBranch}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {branchVersions.length} versions
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-3 overflow-hidden">
        {/* ツールバー */}
        <div className="flex items-center gap-2 pb-2 border-b border-[rgb(var(--border-default))]">
          <Button 
            size="sm" 
            onClick={() => setShowNewVersionDialog(true)}
            className="text-xs"
          >
            <Save className="w-3 h-3 mr-1" />
            保存
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => setShowNewBranchDialog(true)}
            className="text-xs"
          >
            <GitBranch className="w-3 h-3 mr-1" />
            新規ブランチ
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => setCompareMode(!compareMode)}
            className="text-xs"
          >
            <GitMerge className="w-3 h-3 mr-1" />
            比較
          </Button>
        </div>

        {/* ブランチリスト */}
        <div className="flex gap-1 flex-wrap">
          {branches.map(branch => (
            <Button
              key={branch.name}
              size="sm"
              variant={branch.isActive ? "default" : "outline"}
              onClick={() => switchBranch(branch.name)}
              className="text-xs h-7"
            >
              {branch.name}
            </Button>
          ))}
        </div>

        {/* バージョンリスト */}
        <ScrollArea className="flex-1">
          <div className="space-y-2">
            {branchVersions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-[rgb(var(--text-tertiary))]">
                  まだバージョンがありません
                </p>
              </div>
            ) : (
              branchVersions
                .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
                .map((version) => (
                  <div
                    key={version.id}
                    className={`p-3 rounded-lg border ${
                      selectedVersion === version.id
                        ? 'border-[rgb(var(--accent-primary))] bg-[rgb(var(--accent-primary))]/10'
                        : 'border-[rgb(var(--border-default))] bg-[rgb(var(--bg-primary))]'
                    } cursor-pointer transition-all hover:border-[rgb(var(--accent-primary))]/50`}
                    onClick={() => setSelectedVersion(version.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <GitCommit className="w-3 h-3 text-[rgb(var(--text-tertiary))]" />
                          <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                            {version.name}
                          </span>
                          {version.tags?.map(tag => (
                            <Badge key={tag} variant="secondary" className="text-xs h-4">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                        {version.description && (
                          <p className="text-xs text-[rgb(var(--text-secondary))] mb-1">
                            {version.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 text-xs text-[rgb(var(--text-tertiary))]">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {version.author}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {version.timestamp.toLocaleString('ja-JP')}
                          </span>
                        </div>
                      </div>
                      {selectedVersion === version.id && (
                        <div className="flex items-center gap-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            className="w-7 h-7"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRestore(version.id);
                            }}
                            title="復元"
                          >
                            <RotateCcw className="w-3 h-3" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="w-7 h-7"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteVersion(version.id);
                            }}
                            title="削除"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                    </div>
                    {compareMode && (
                      <div className="mt-2 flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={compareVersions.includes(version.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              if (!compareVersions[0]) {
                                setCompareVersions([version.id, null]);
                              } else if (!compareVersions[1]) {
                                setCompareVersions([compareVersions[0], version.id]);
                              }
                            } else {
                              setCompareVersions(prev => 
                                prev.map(v => v === version.id ? null : v) as [string | null, string | null]
                              );
                            }
                          }}
                          className="w-3 h-3"
                        />
                        <span className="text-xs text-[rgb(var(--text-tertiary))]">
                          比較対象として選択
                        </span>
                      </div>
                    )}
                  </div>
                ))
            )}
          </div>
        </ScrollArea>

        {/* 比較モード時のアクション */}
        {compareMode && compareVersions[0] && compareVersions[1] && (
          <div className="pt-2 border-t border-[rgb(var(--border-default))]">
            <Button 
              size="sm" 
              onClick={handleCompare}
              className="w-full text-xs"
            >
              <GitMerge className="w-3 h-3 mr-1" />
              選択したバージョンを比較・マージ
            </Button>
          </div>
        )}

        {/* 新規バージョン作成ダイアログ */}
        {showNewVersionDialog && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[rgb(var(--bg-primary))] p-4 rounded-lg border border-[rgb(var(--border-default))] w-80">
              <h3 className="text-sm font-medium mb-3">新しいバージョンを保存</h3>
              <input
                type="text"
                placeholder="バージョン名"
                value={versionName}
                onChange={(e) => setVersionName(e.target.value)}
                className="w-full px-3 py-2 mb-2 text-sm bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded"
              />
              <textarea
                placeholder="説明（オプション）"
                value={versionDescription}
                onChange={(e) => setVersionDescription(e.target.value)}
                className="w-full px-3 py-2 mb-3 text-sm bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded resize-none"
                rows={3}
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={createVersion} className="flex-1">
                  保存
                </Button>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => setShowNewVersionDialog(false)}
                  className="flex-1"
                >
                  キャンセル
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* 新規ブランチ作成ダイアログ */}
        {showNewBranchDialog && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-[rgb(var(--bg-primary))] p-4 rounded-lg border border-[rgb(var(--border-default))] w-80">
              <h3 className="text-sm font-medium mb-3">新しいブランチを作成</h3>
              <input
                type="text"
                placeholder="ブランチ名"
                value={branchName}
                onChange={(e) => setBranchName(e.target.value)}
                className="w-full px-3 py-2 mb-3 text-sm bg-[rgb(var(--bg-secondary))] border border-[rgb(var(--border-default))] rounded"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={createBranch} className="flex-1">
                  作成
                </Button>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => setShowNewBranchDialog(false)}
                  className="flex-1"
                >
                  キャンセル
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}