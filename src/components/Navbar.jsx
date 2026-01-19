import { useState, useEffect } from 'react';

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-slate-900/90 backdrop-blur-xl shadow-lg'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 py-5 flex justify-between items-center">
        <div className="flex items-center gap-2 text-xl font-bold cursor-pointer">
          <span className="text-4xl">🔥</span>
          <span>FIREWATCH</span>
        </div>
        <ul className="hidden md:flex gap-8 text-sm font-medium">
          <li>
            <a href="#problema" className="text-slate-300 hover:text-blue-400 transition-colors">
              El Problema
            </a>
          </li>
          <li>
            <a href="#solucion" className="text-slate-300 hover:text-blue-400 transition-colors">
              Solución
            </a>
          </li>
          <li>
            <a href="#tecnologia" className="text-slate-300 hover:text-blue-400 transition-colors">
              Tecnología
            </a>
          </li>
          <li>
            <a href="#proceso" className="text-slate-300 hover:text-blue-400 transition-colors">
              Proceso
            </a>
          </li>
          <li>
            <a href="#faq" className="text-slate-300 hover:text-blue-400 transition-colors">
              FAQ
            </a>
          </li>
        </ul>
        <a
          href="#contacto"
          className="px-6 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg font-medium transition-all hover:scale-105"
        >
          📅 Agendar Reunión
        </a>
      </div>
    </nav>
  );
};

export default Navbar;
