import React, {useState, useEffect} from 'react';

export default function IntroScreen({onEnter}){
    const [displayedText, setDisplayedText] = useState("");
    const [visible, setVisible] = useState(false);
    const [done, setDone] = useState(false);

    useEffect(() => {
        setTimeout(() => {
            setVisible(true);
          }, 200);
      }, []);

      useEffect(() => {
        if (!visible) return;
        const text = "Your AI powered English tutor";
        let i = 0;
        let started = false;

        const timeout = setTimeout(() => {
            started = true;
    
            const interval = setInterval(() => {
                setDisplayedText(text.slice(0, i));
                i++;
    
                if (i > text.length) {
                    clearInterval(interval);
                    setDone(true);
                }
            }, 80);
        }, 800);
    
        return () => clearTimeout(timeout);
    }, [visible]);

    return(
        <div className="h-full w-full flex items-center justify-center">
            <div className={`
                    flex flex-col items-center gap-6
                    bg-white/40 backdrop-blur-xl px-12 py-14
                    rounded-3xl shadow-xl border border-white/50
                    animate-[breathe_8s_ease-in-out_infinite]
                    transition-all duration-2000 ease-in-out
                    ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}
                    `}>
                    <h1 className= "text-emerald-700 text-8xl font-medium drop-shadow-sm tracking-tighter mb-3"> jaide </h1>
                    <h2 className="text-slate-600 text-xl mt-6 tracking-wide mb-3">{displayedText}
                        <span className={done ? "opacity-0" : "animate-pulse"}>|</span>
                    </h2>
                    <div className={`
                        transition-all duration-1000 ease-in-out
                        ${done
                        ? "opacity-100 translate-y-0"
                        : "opacity-0 translate-y-4 pointer-events-none"
                        }
                    `}>
                        <button
                        onClick={onEnter}
                        className="
                        text-emerald-700 font-semibold text-3xl
                        py-4 px-10 rounded-2xl
                    
                        bg-emerald-100/40
                        backdrop-blur-xl
                        border border-emerald-200/50
                    
                        shadow-lg
                        hover:scale-105
                        hover:bg-emerald-200/50
                        hover:shadow-xl
                    
                        active:scale-95
                        transition-all duration-200 ease-out
                        "
                        >
                        Let's Practice
                        </button>
                    </div> 
            </div>
        </div>
    )
}