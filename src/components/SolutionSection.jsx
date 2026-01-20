import { motion } from 'framer-motion';

const solutions = [
  {
    step: '01',
    title: 'Detección',
    subtitle: 'De 3-4 horas → Menos de 5 minutos',
    description: 'Cámaras térmicas de última generación detectan temperaturas anómalas hasta 2 horas antes de que sean visibles. Nuestra IA filtra falsos positivos en tiempo real.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
    color: 'orange'
  },
  {
    step: '02',
    title: 'Coordinación',
    subtitle: 'De equipos aislados → Command Center',
    description: 'Panel único donde autoridades ven todos los incendios activos, drones disponibles y recursos de respuesta. Sin intermediarios, sin demoras.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    color: 'blue'
  },
  {
    step: '03',
    title: 'Respuesta',
    subtitle: 'De "esperamos noticias" → Evacuación proactiva',
    description: 'Con alerta anticipada, las poblaciones se evacúan antes de que llegue el fuego. Hospitales preparan recursos. Bomberos se posicionan estratégicamente.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: 'green'
  }
];

const SolutionSection = () => {
  return (
    <section id="solucion" className="bg-gradient-to-b from-slate-950 to-slate-900 py-24">
      <div className="container mx-auto px-4 max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-orange-500 uppercase text-sm font-bold tracking-wider">La Solución</span>
          <h2 className="text-4xl md:text-5xl font-bold mt-4">
            <span className="text-green-400">Detectar antes.</span>{' '}
            <span className="text-blue-400">Responder mejor.</span>
          </h2>
          <p className="text-xl text-slate-300 mt-6 max-w-3xl mx-auto">
            No es solo tecnología. Es una arquitectura de toma de decisiones
            que transforma la forma en que Chile responde a emergencias forestales.
          </p>
        </motion.div>

        {/* Solution cards */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {solutions.map((solution, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.15 }}
              viewport={{ once: true }}
              className="relative bg-slate-900/50 border border-slate-800 rounded-xl p-8 hover:border-slate-700 transition-all group"
            >
              {/* Step number */}
              <div className="absolute -top-4 -left-4 w-12 h-12 bg-slate-950 border border-slate-700 rounded-lg flex items-center justify-center">
                <span className={`font-bold ${
                  solution.color === 'orange' ? 'text-orange-400' :
                  solution.color === 'blue' ? 'text-blue-400' :
                  'text-green-400'
                }`}>
                  {solution.step}
                </span>
              </div>

              {/* Icon */}
              <div className={`w-14 h-14 rounded-lg flex items-center justify-center mb-6 ${
                solution.color === 'orange' ? 'bg-orange-500/20 text-orange-400' :
                solution.color === 'blue' ? 'bg-blue-500/20 text-blue-400' :
                'bg-green-500/20 text-green-400'
              }`}>
                {solution.icon}
              </div>

              <h3 className="text-2xl font-bold text-white mb-2">
                {solution.title}
              </h3>

              <p className={`text-sm font-semibold mb-4 ${
                solution.color === 'orange' ? 'text-orange-400' :
                solution.color === 'blue' ? 'text-blue-400' :
                'text-green-400'
              }`}>
                {solution.subtitle}
              </p>

              <p className="text-slate-300 leading-relaxed">
                {solution.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Comparison visual */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true }}
          className="bg-slate-900/30 border border-slate-800 rounded-2xl p-8 md:p-12"
        >
          <h3 className="text-2xl font-bold text-center mb-8">
            La diferencia que salva vidas
          </h3>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Before */}
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-red-400">Sin PyroGuard</h4>
              </div>
              <ul className="space-y-3 text-slate-300">
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  Detección: 3-4 horas después del inicio
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  Coordinación: Llamadas fragmentadas entre agencias
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  Evacuación: Reactiva, caótica, tardía
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  Resultado: Megaincendios, vidas perdidas
                </li>
              </ul>
            </div>

            {/* After */}
            <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-green-400">Con PyroGuard</h4>
              </div>
              <ul className="space-y-3 text-slate-300">
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  Detección: Menos de 5 minutos
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  Coordinación: Panel único, tiempo real
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  Evacuación: Proactiva, ordenada, segura
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  Resultado: Incendios contenidos, vidas salvadas
                </li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default SolutionSection;
