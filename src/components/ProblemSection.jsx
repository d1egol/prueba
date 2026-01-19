import { motion } from 'framer-motion';

const problems = [
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'Tiempo Perdido',
    stat: '3-4 horas',
    statLabel: 'tiempo promedio de detección',
    description: 'Los incendios pequeños se convierten en megaincendios antes de que alguien los detecte. En 2024, este retraso costó vidas.',
    color: 'red'
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'Costo de Inacción',
    stat: '$500M+',
    statLabel: 'en daños anuales por incendios',
    description: 'Pérdida de ecosistemas irreversible. Impacto en infraestructura vital: líneas de energía, rutas, viviendas y vidas humanas.',
    color: 'orange'
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
    title: 'Capacidad Limitada',
    stat: '<20%',
    statLabel: 'cobertura nocturna efectiva',
    description: 'Recursos de vigilancia humana agotados. Respuesta descentralizada e ineficiente. Sin visión térmica nocturna.',
    color: 'yellow'
  }
];

const stats = [
  { value: '132', label: 'Vidas perdidas en Valparaíso 2024' },
  { value: '5,500+', label: 'Hectáreas quemadas en 48 horas' },
  { value: '70%', label: 'De incendios detectados tarde' }
];

const ProblemSection = () => {
  return (
    <section id="problema" className="bg-slate-950 py-24">
      <div className="container mx-auto px-4 max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-orange-500 uppercase text-sm font-bold tracking-wider">El Problema</span>
          <h2 className="text-4xl md:text-5xl font-bold mt-4">
            La ventana de reacción:{' '}
            <span className="text-red-500">cada minuto cuenta</span>
          </h2>
          <p className="text-xl text-slate-300 mt-6 max-w-3xl mx-auto">
            Chile enfrenta una crisis de incendios forestales que escala cada temporada.
            El problema no es solo el fuego — es el tiempo que tardamos en detectarlo.
          </p>
        </motion.div>

        {/* Stats bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="grid md:grid-cols-3 gap-6 mb-16"
        >
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center"
            >
              <div className="text-4xl md:text-5xl font-bold text-red-400 mb-2">
                {stat.value}
              </div>
              <div className="text-slate-300 text-sm">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>

        {/* Problem cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {problems.map((problem, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 hover:border-slate-700 transition-all"
            >
              <div className={`w-14 h-14 rounded-lg flex items-center justify-center mb-6 ${
                problem.color === 'red' ? 'bg-red-500/20 text-red-400' :
                problem.color === 'orange' ? 'bg-orange-500/20 text-orange-400' :
                'bg-yellow-500/20 text-yellow-400'
              }`}>
                {problem.icon}
              </div>

              <h3 className="text-xl font-bold text-white mb-2">
                {problem.title}
              </h3>

              <div className="mb-4">
                <span className={`text-3xl font-bold ${
                  problem.color === 'red' ? 'text-red-400' :
                  problem.color === 'orange' ? 'text-orange-400' :
                  'text-yellow-400'
                }`}>
                  {problem.stat}
                </span>
                <span className="text-slate-400 text-sm ml-2">
                  {problem.statLabel}
                </span>
              </div>

              <p className="text-slate-300 leading-relaxed">
                {problem.description}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          viewport={{ once: true }}
          className="mt-16 text-center"
        >
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            La pregunta no es <strong className="text-white">si habrá otro megaincendio</strong>,
            sino <strong className="text-orange-400">cuándo</strong> — y si estaremos preparados para detectarlo a tiempo.
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default ProblemSection;
