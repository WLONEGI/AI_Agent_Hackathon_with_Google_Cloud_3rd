'use client';

import React from 'react';
import { type CharacterData } from '@/types/processing';

interface CharacterPreviewProps {
  data: CharacterData;
}

const CharacterPreview: React.FC<CharacterPreviewProps> = ({ data }) => {
  return (
    <div className="p-4" role="region" aria-labelledby="character-preview-title">
      <div id="character-preview-title" className="sr-only">キャラクター設定プレビュー</div>
      {data.imageUrl ? (
        <img 
          src={data.imageUrl} 
          alt={`キャラクター「${data.characters?.[0]?.name || '不明'}」のデザイン`}
          className="w-full h-auto rounded opacity-80"
          role="img"
          loading="lazy"
        />
      ) : (
        <div className="grid grid-cols-1 gap-3" role="list" aria-label="キャラクター一覧">
          {data.characters?.map((char, index: number) => (
            <div key={index} className="bg-[rgb(var(--bg-tertiary))] p-3 rounded" role="listitem">
              <div className="text-xs text-[rgb(var(--text-primary))] font-medium">{char.name}</div>
              <div className="text-xs text-[rgb(var(--text-secondary))]">{char.role}</div>
              {char.appearance && (
                <div className="text-xs text-[rgb(var(--text-tertiary))] mt-1">{char.appearance}</div>
              )}
              {char.personality && (
                <div className="text-xs text-[rgb(var(--text-tertiary))] mt-1">性格: {char.personality}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CharacterPreview;