import React, { useState, useEffect, useRef } from 'react';
import PronunciationPanel from './PronunciationPanel';
import { FaMicrophone, FaStop, FaVolumeUp } from "react-icons/fa";
import { PiLeafFill } from "react-icons/pi";

export default function PronunciationTraining() {
    const [isRecording, setIsRecording] = useState(false);
    const [scoreData, setScoreData] = useState(null);
    const [sentenceData, setSentenceData] = useState({ text: "", phonemes: "" });
    const [visible, setVisible] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [fadeKey, setFadeKey] = useState(0);
    const [activePanelInfo, setActivePanelInfo] = useState(null);
    const [selectedWord, setSelectedWord] = useState(null);
    const [selectedPhonemes, setSelectedPhonemes] = useState([]);
    const [panelOpen, setPanelOpen] = useState(false);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const API_BASE_URL = "https://froglover54-pronunciation-backend.hf.space";

    const nextSentence = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/get_sentence`);
            const data = await response.json();
    
            setSentenceData({
                text: data.sentence,
                phonemes: data.sentence_phonemes,
            });
    
            setScoreData(null);
    
            // force re-animation
            setFadeKey(prev => prev + 1);
    
        } catch (err) {
            console.error(err);
        }
    };

    const playAudio = (text) => {
        const url = `${API_BASE_URL}/tts?text=${encodeURIComponent(text)}&voice=en-US-AriaNeural`;
        const audio = new Audio(url);
        audio.play();
    };

    const toggleRecording = async () => {
        if (!isRecording) {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                setIsProcessing(true);
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'user_audio.wav');
                formData.append('current_text', sentenceData.text);
                const response = await fetch(`${API_BASE_URL}/score`, { method: 'POST', body: formData });
                const data = await response.json();
                setScoreData(data);
                setIsProcessing(false);
            };

            mediaRecorder.start();
            setIsRecording(true);
        } else {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
    };

    const renderHighlightedText = () => {
        if (!scoreData || !scoreData.incorrect_indices) {
            return <span className="text-slate-700">{sentenceData.text}</span>;
        }
        const textErrorMap = {};
        scoreData.incorrect_indices.forEach(item => { textErrorMap[item[0]] = item[1]; });
        return sentenceData.text.split('').map((char, index) => {
            const severity = textErrorMap[index];
            let color = "text-emerald-500";
            if (severity === "incorrect") color = "text-red-400";
            if (severity === "partial") color = "text-amber-300";
            return <span key={index} className={color}>{char}</span>;
        });
    };

    const getWordAtIndex = (text, index) => {
        const left = text.lastIndexOf(' ', index) + 1;
        const right = text.indexOf(' ', index);
    
        return text.substring(
            left,
            right === -1 ? text.length : right
        );
    };

    const getWordInfo = (word) => {
        return scoreData.word_feedback.find(w => w.word === word);
    };

    const renderInteractiveText = () => {
        if (!scoreData?.word_feedback) {
            return <span className="text-slate-700">{sentenceData.text}</span>;
        }

        const textErrorMap = new Map(scoreData.incorrect_indices);
        const elements = [];
        let currentIdx = 0;
        const fullText = sentenceData.text;

        scoreData.word_feedback.forEach((wordItem, wIndex) => {
            // space before and after word
            if (wordItem.char_start_index > currentIdx) {
                const textBefore = fullText.substring(currentIdx, wordItem.char_start_index);
                elements.push(
                    <span key={`space-${wIndex}`} className="text-slate-700 whitespace-pre-wrap">
                        {textBefore}
                    </span>
                );
            }

            // calc severities
            const charSeverities = wordItem.word.split('').map((char, cIndex) => {
                const globalIndex = wordItem.char_start_index + cIndex;
                return textErrorMap.get(globalIndex);
            });

            // render severities
            const chars = wordItem.word.split('').map((char, cIndex) => {
                const severity = charSeverities[cIndex];
                
                let color = "text-emerald-500";
                if (severity === "incorrect") color = "text-red-400";
                if (severity === "partial") color = "text-amber-400";

                return <span key={`char-${wIndex}-${cIndex}`} className={color}>{char}</span>;
            });

            // creating clickable word
            elements.push(
                <span 
                    key={`word-${wIndex}`} 
                    className="cursor-pointer transition-opacity hover:opacity-70" 
                    onClick={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        setActivePanelInfo({
                            word: wordItem.word,
                            phonemes: wordItem.phonemes,
                            charSeverities: charSeverities,
                            position: { x: rect.left, y: rect.bottom + 10 }
                        });
                    }}
                >
                    {chars}
                </span>
            );
            currentIdx = wordItem.char_end_index;
        });

        // any punctuation
        if (currentIdx < fullText.length) {
            const trailingText = fullText.substring(currentIdx);
            elements.push(
                <span key={`trail-${currentIdx}`} className="text-slate-700 whitespace-pre-wrap">
                    {trailingText}
                </span>
            );
        }

        return elements;
    };

    const renderHighlightedPhonemes = () => {
        if (!scoreData || !scoreData.phoneme_indices) {
            return <span className="text-slate-400">{sentenceData.phonemes}</span>;
        }
        const phonemeErrorMap = {};
        scoreData.phoneme_indices.forEach(item => { phonemeErrorMap[item[0]] = item[1]; });
        const phonemeArray = Array.isArray(sentenceData.phonemes)
            ? sentenceData.phonemes
            : sentenceData.phonemes.split('');
        return phonemeArray.map((phoneme, index) => {
            const severity = phonemeErrorMap[index];
            let color = "text-emerald-500";
            if (severity === "incorrect") color = "text-red-400";
            if (severity === "partial") color = "text-amber-300";
            return <span key={`phone-${index}`} className={color}>{phoneme}</span>;
        });
    };

    function LoadingDots() {
        return (
            <div className="flex gap-2 h-16 items-center">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
            </div>
        );
    }

    useEffect(() => { nextSentence(); }, []);

    return (
        <div className="
        h-full w-full
        flex flex-col
        items-center
        gap-6
        px-4
        pt-10
        pb-20
        overflow-y-auto
      ">
            <div className="w-full max-w-2xl flex flex-col gap-4">
                

                {scoreData ? (<div className= "text-slate-60 text-center"> Click a word for detailed feedback!</div>) : (<div className= "text-slate-60 text-center"> Try saying this </div>)}
                {/* sentence box */}
                <div className="w-full">
                    <div className="flex items-center justify-between w-full mb-3">
                        <p className="text-sm text-slate-400 tracking-widest">Sentence</p>
                        
                        <button 
                            onClick={() => playAudio(sentenceData.text)} 
                            className="p-3 border-2 border-amber-300 bg-white/40 hover:bg-amber-50 text-amber-700 hover:text-amber-900 cursor-pointer shadow-sm rounded-full transition-all duration-200 active:scale-95 flex items-center justify-center"
                            aria-label="Play audio"
                        >
                            <FaVolumeUp size={18} />
                        </button>
                    </div>
                    
                    {/* text */}
                    <div className="bg-white/50 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg p-8 min-h-[110px] break-words">
                        <div
                            key={fadeKey}
                            className="
                                text-xl leading-relaxed
                                opacity-0
                                animate-fadeInSentence
                            "
                        >
                            {renderInteractiveText()}
                        </div>
                    </div>
                </div>
                
                {/* phoneme box */}
                <div>
                    <p className="text-sm text-slate-400 tracking-widest mb-3 ml-1">
                        Phonemes
                    </p>
                    <div className="bg-white/50 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg p-8 min-h-[110px] break-words">
                        <div className="text-lg leading-relaxed opacity-0 animate-fadeInSentence">
                            {renderHighlightedPhonemes()}
                        </div>
                    </div>
                </div>

            </div>

            {/* legend */}
            {scoreData && (
                <div className="flex gap-6 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                        <span className="text-emerald-500">●</span> correct
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="text-amber-400">●</span> partial
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="text-red-400">●</span> incorrect
                    </span>
                </div>
            )}

            {/* controls */}
            {isProcessing ? (
                <LoadingDots/>
            ) : (<div className="flex gap-4">
            <button
                onClick={toggleRecording}
                className={`
                w-16 h-16
                rounded-full
                cursor-pointer
                flex items-center justify-center
                transition-all duration-200
                hover:scale-105
                active:scale-95
                shadow-sm
                ${isRecording
                                    ? "bg-red-500 hover:bg-red-600 animate-pulse"
                                    : "bg-emerald-500 hover:bg-emerald-600"
                                }
                `}
            >
                {isRecording ? <FaStop size={20} color="white" /> : <FaMicrophone size={24} color="white" />}
            </button>

            <button
                onClick={nextSentence}
                disabled={isRecording}
                className={`
                    px-8 py-4 rounded-2xl text-base font-semibold 
                    border-2
                    transition-all duration-200
                    ${
                        isRecording
                            ? "bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed opacity-60"
                            : "bg-white/40 border-amber-300 text-amber-700 hover:bg-amber-50  hover:text-amber-900 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
                    }
                `}
            >
                Next →
            </button> </div>)}
                {activePanelInfo && (
                    <PronunciationPanel 
                        word={activePanelInfo.word}
                        phonemes={activePanelInfo.phonemes}
                        charSeverities={activePanelInfo.charSeverities}
                        position={activePanelInfo.position}
                        onClose={() => setActivePanelInfo(null)}
                    />
                )}
        </div>
    );
}
