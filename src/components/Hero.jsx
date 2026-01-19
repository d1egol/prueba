import { motion } from 'framer-motion';

const Hero = () => {
  const stats = [
    { number: '132', label: 'vidas perdidas en Valparaíso 2024' },
    { number: '5,500ha', label: 'quemadas en solo 2 horas' },
    { number: '<5min', label: 'alerta temprana posible' },
  ];

  const heroGallery = [
    {
      src: 'https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=600&q=80',
      label: '🚁 Patrullaje 24/7',
    },
    {
      src: 'https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=600&q=80',
      label: '🌡️ Detección Térmica',
    },
    {
      src: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&q=80',
      label: '⚡ Control Real-Time',
    },
  ];

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1448375240586-882707db888b?w=1920&q=80')",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/95 via-slate-900/80 to-slate-950/95" />

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 py-32 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-sm mb-8"
        >
          <span>🇩🇪</span>
          <span>Tecnología alemana · Soluciones a medida para Chile</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-4xl md:text-6xl font-bold leading-tight mb-6"
        >
          Protegemos los bosques de Chile
          <br />
          <span className="bg-gradient-to-r from-orange-400 to-green-400 bg-clip-text text-transparent">
            antes de que sea tarde
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-xl text-slate-300 max-w-3xl mx-auto mb-12"
        >
          Sistema de detección y respuesta temprana a incendios forestales con drones autónomos e
          inteligencia artificial. Proyectos diseñados a medida para tu operación.
        </motion.p>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12"
        >
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6"
            >
              <div className="text-4xl font-bold text-orange-500 font-mono mb-2">
                {stat.number}
              </div>
              <div className="text-sm text-slate-400">{stat.label}</div>
            </div>
          ))}
        </motion.div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex flex-wrap gap-4 justify-center mb-8"
        >
          <a
            href="#contacto"
            className="px-8 py-3 bg-orange-500 hover:bg-orange-600 rounded-lg font-medium transition-all hover:scale-105"
          >
            📅 Agendar Reunión Estratégica
          </a>
          <a
            href="#solucion"
            className="px-8 py-3 border-2 border-slate-700 hover:border-blue-400 hover:text-blue-400 rounded-lg font-medium transition-all"
          >
            Conocer la Solución →
          </a>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-sm text-slate-400 mb-12"
        >
          🇩🇪 Socio tecnológico: <strong className="text-slate-300">Dronivo (Alemania)</strong>
        </motion.p>

        {/* Hero Gallery */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <p className="text-center text-blue-400 font-semibold text-sm mb-4">
            TECNOLOGÍA EN ACCIÓN
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            {heroGallery.map((item, index) => (
              <div
                key={index}
                className="relative rounded-xl overflow-hidden border-2 border-slate-800 hover:border-orange-500 transition-all duration-300 aspect-video group cursor-pointer"
              >
                <img src={item.src} alt={item.label} className="w-full h-full object-cover" />
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black to-transparent">
                  <div className="text-sm font-semibold text-orange-400 uppercase tracking-wide">
                    {item.label}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
