import { motion } from 'framer-motion';

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background - Drone en acción */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('/images/drone-fire.jpg')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/80 via-slate-900/70 to-slate-950/90" />

      {/* Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 py-24 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl md:text-6xl font-bold leading-tight mb-6"
        >
          Detectamos incendios
          <br />
          <span className="bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
            antes de que sea tarde
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl text-slate-300 max-w-2xl mx-auto mb-8"
        >
          Drones autónomos con IA para detección temprana, monitoreo 24/7
          y despliegue de gel retardante.
        </motion.p>

        {/* Stats simples */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap justify-center gap-8 mb-10"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-500">&lt;5 min</div>
            <div className="text-sm text-slate-400">detección</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400">24/7</div>
            <div className="text-sm text-slate-400">monitoreo</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400">100%</div>
            <div className="text-sm text-slate-400">autónomo</div>
          </div>
        </motion.div>

        {/* CTA principal */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-wrap gap-4 justify-center"
        >
          <a
            href="#contacto"
            className="px-8 py-4 bg-orange-500 hover:bg-orange-600 rounded-lg font-bold text-lg transition-all hover:scale-105"
          >
            Solicitar Demo
          </a>
          <a
            href="#servicios"
            className="px-8 py-4 border-2 border-slate-600 hover:border-orange-500 rounded-lg font-medium transition-all"
          >
            Ver Servicios
          </a>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
