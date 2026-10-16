import { FaLeaf } from "react-icons/fa";
import { LuSettings } from 'react-icons/lu'

export default function Header() {
    return (
        <header
            className="
            h-16
            px-8
            flex
            items-center
            justify-between
            bg-white/30
            backdrop-blur-xl
            border-b
            border-white/40
            shadow-sm
            "
        >
            {/* logo */}
            <div className="flex items-center gap-2">
                <FaLeaf className="text-emerald-500 text-lg" />
                <h1 className="text-2xl font-semibold tracking-tight text-emerald-700">
                    jaide
                </h1>
            </div>

            {/* tabs */}
            <nav className="flex gap-2">
                <button
                    className="
                    px-4 py-2 rounded-xl
                    bg-emerald-100
                    text-emerald-700
                    font-medium
                    cursor-default
                    "
                >
                    Practice
                </button>

                <button
                    className="
                    px-4 py-2 rounded-xl
                    text-slate-500
                    hover:bg-amber-500/40
                    transition
                    cursor-default
                    "
                >
                    Progress
                </button>

                <button
                    className="
                    px-4 py-2 rounded-xl
                    text-slate-500
                    hover:bg-amber-500/40
                    transition
                    cursor-default
                    "
                >
                    <LuSettings size={24} color="#666" />
                </button>
            </nav>
        </header>
    );
}