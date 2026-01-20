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
        scrolled ? 'bg-slate-900/95 backdrop-blur-xl shadow-lg' : 'bg-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
        <a href="#" className="flex items-center gap-2 text-xl font-bold">
          <span className="text-3xl">🔥</span>
          <span>DRONEWATCH</span>
        </a>
        <ul className="hidden md:flex gap-6 text-sm">
          <li><a href="#servicios" className="text-slate-300 hover:text-orange-400 transition-colors">Servicios</a></li>
          <li><a href="#faq" className="text-slate-300 hover:text-orange-400 transition-colors">FAQ</a></li>
          <li><a href="#contacto" className="text-slate-300 hover:text-orange-400 transition-colors">Contacto</a></li>
        </ul>
        <a
          href="#contacto"
          className="px-5 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg font-medium transition-all text-sm"
        >
          Solicitar Demo
        </a>
      </div>
    </nav>
  );
};

export default Navbar;
