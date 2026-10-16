import React, { useState, useEffect, useRef } from 'react';
import { useMemo } from 'react';
import { DESCRIPTIONS, AFFIRMATIONS } from './phonemeFeedback';
import { FaMicrophone, FaStop, FaVolumeUp } from "react-icons/fa";

export default function PronunciationPanel({ word, phonemes, charSeverities, position, onClose }) {
    const panelRef = useRef(null);
  
    useEffect(() => {
      function handleClickOutside(event) {
        if (panelRef.current && !panelRef.current.contains(event.target)) {
          onClose();
        }
      }
      setTimeout(() => document.addEventListener('mousedown', handleClickOutside), 50);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [onClose]);

    const feedbackTexts = useMemo(() => {
      return phonemes.map((p) => {
          if (p.severity === 'correct') {
              return AFFIRMATIONS[Math.floor(Math.random() * AFFIRMATIONS.length)];
          }
          const description = DESCRIPTIONS[p.phoneme] ?? "This phoneme needs attention.";
          return p.severity === 'partial' ? `Close! ${description}` : description;
      });
  }, [phonemes]);

    const getColor = (severity) => {
      if (severity === 'incorrect') return 'text-red-400';
      if (severity === 'partial') return 'text-amber-400';
      return 'text-emerald-500';
    };
  
    const playAudio = (text) => {
      const url = `${API_BASE_URL}/tts?text=${encodeURIComponent(text)}&voice=en-US-AriaNeural`;
      const audio = new Audio(url);
      audio.play();
    };
  
    return (
      <div 
        ref={panelRef}
        className="fixed z-[9999] w-80 bg-white/95 backdrop-blur-xl border border-slate-200 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-fadeIn"
        style={{ 
          top: position.y, 
          left: position.x,
          maxWidth: 'calc(100vw - 20px)'
        }}
      >
        <style>{`
          .always-show-scroll::-webkit-scrollbar {
            width: 6px;
          }
          .always-show-scroll::-webkit-scrollbar-track {
            background: transparent;
          }
          .always-show-scroll::-webkit-scrollbar-thumb {
            background-color: #cbd5e1;
            border-radius: 20px;
          }
        `}</style>
  
        {/* header */}
        <div className="p-5 bg-slate-50 border-b border-slate-100 flex justify-between items-start">
          <div>
            <h3 className="text-2xl font-bold tracking-wide mb-1 flex">
              {word.split('').map((char, i) => (
                <span key={i} className={getColor(charSeverities?.[i])}>
                  {char}
                </span>
              ))}
            </h3>
            <div className="text-xl font-mono text-slate-500 flex space-x-[2px]">
              <span>/</span>
              {phonemes.map((p, i) => (
                <span key={i} className={`font-bold ${getColor(p.severity)}`}>
                  {p.phoneme}
                </span>
              ))}
              <span>/</span>
            </div>
          </div>
            <button 
                onClick={() => playAudio(word)} 
                className="p-3 border-2 border-amber-300 bg-white/40 hover:bg-amber-50 text-amber-700 hover:text-amber-900 cursor-pointer shadow-sm rounded-full transition-all duration-200 active:scale-95 flex items-center justify-center"
                aria-label="Play audio"
                >
                <FaVolumeUp size={18} />
            </button>
        </div>
        <div className="max-h-64 overflow-y-auto always-show-scroll p-5 pr-3 space-y-4">
        {phonemes.map((p, i) => (
            <div key={i} className="flex flex-col">
                <span className={`text-xl font-bold font-mono ${getColor(p.severity)}`}>
                    /{p.phoneme}/
                </span>
                <span className="text-sm text-slate-600 mt-1 leading-relaxed">
                    {feedbackTexts[i]}
                </span>
            </div>
        ))}
        </div>
      </div>
    );
  }