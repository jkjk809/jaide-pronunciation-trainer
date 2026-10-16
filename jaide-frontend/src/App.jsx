import React, { useState } from 'react';
import IntroScreen from './IntroScreen';
import PronunciationTraining from './PronunciationTraining';
import { FaGithub } from 'react-icons/fa';
import Header from "./Header";

export default function App() {
  const [screen, setScreen] = useState("intro");
  const [fade, setFade] = useState(false);

  const handleEnter = () => {
    setFade(true);

    setTimeout(() => {
      setScreen("training");
      setFade(false);
    }, 700);
  };

  return (
    <div className="h-screen w-screen relative flex flex-col overflow-hidden">

      {/* BACKGROUNDS  */}
      <div
        className={`
          absolute inset-0 z-0
          bg-gradient-to-r from-orange-100 via-emerald-50 to-yellow-100
          bg-[length:200%_200%]
          animate-[gradientMove_18s_ease-in-out_infinite]
          transition-opacity duration-700
          ${screen === "intro" ? "opacity-100" : "opacity-0"}
        `}
      />

      <div
        className={`
          absolute inset-0 z-0
          bg-gradient-to-br from-orange-100 via-emerald-50 to-yellow-100
          transition-opacity duration-700
          ${screen === "training" ? "opacity-100" : "opacity-0"}
        `}
      />
      

      {/* MAIN */}
      <div className="relative z-10 flex-1 w-full">

        {screen === "intro" && (
          <div
            className={`
              h-full w-full flex items-center justify-center
              transition-opacity duration-700
              ${fade ? "opacity-0" : "opacity-100"}
            `}
          >
            <IntroScreen onEnter={handleEnter} />
          </div>
        )}

        {screen === "training" && (
          <div className="h-full w-full animate-fadeIn">
            <Header></Header>
            <PronunciationTraining />
          </div>
        )}

      </div>

      {/* footer */}
      <footer className="relative z-10 w-full py-5 flex justify-center text-sm text-slate-400">
        <a
          href="https://github.com/jkjk809"
          target="_blank"
          className="flex items-center gap-2 hover:text-slate-600 transition"
        >
          <FaGithub size={18} />
          GitHub
        </a>
      </footer>

    </div>
  );
}