const Footer = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-800 py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex items-center justify-center gap-2 text-xl font-bold mb-8">
          <span className="text-4xl">🔥</span>
          <span>PYROGUARD</span>
        </div>
        <div className="text-center text-slate-400 text-sm">
          <p>© 2026 PyroGuard Chile. Todos los derechos reservados.</p>
          <p className="mt-2">
            🇩🇪 Socio tecnológico: <strong className="text-slate-300">Dronivo</strong>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
