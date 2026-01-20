import { motion } from 'framer-motion';

const ThermalShowcase = () => {
  const services = [
    {
      src: '/images/thermal-forest.jpg',
      title: 'Detección Térmica',
      desc: 'Cámara 640x512 que detecta diferencias de 0.1°C',
    },
    {
      src: '/images/dji-interface.png',
      title: 'Monitoreo 24/7',
      desc: 'Operación día y noche, incluso con humo denso',
    },
    {
      src: '/images/mapa-incendios.png',
      title: 'Mapeo en Tiempo Real',
      desc: 'Identificación de zonas de riesgo y hotspots',
    },
  ];

  const specs = [
    { value: '640×512', label: 'Resolución térmica' },
    { value: '45 min', label: 'Tiempo de vuelo' },
    { value: '30 seg', label: 'Despliegue' },
    { value: '<1 kg', label: 'Peso del drone' },
  ];

  return (
    <section id="servicios" className="bg-slate-950 py-20">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Tecnología <span className="text-orange-500">DJI Mavic 3T</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            El drone térmico más avanzado para detección de incendios
          </p>
        </motion.div>

        {/* Specs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12"
        >
          {specs.map((spec, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-500">{spec.value}</div>
              <div className="text-xs text-slate-400 mt-1">{spec.label}</div>
            </div>
          ))}
        </motion.div>

        {/* Services Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {services.map((service, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group rounded-xl overflow-hidden border border-slate-800 hover:border-orange-500 transition-all bg-slate-900"
            >
              <div className="aspect-video overflow-hidden">
                <img
                  src={service.src}
                  alt={service.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <div className="p-5">
                <h3 className="text-lg font-bold text-white mb-2">{service.title}</h3>
                <p className="text-slate-400 text-sm">{service.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Gel Retardante */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-2xl p-6 text-center mb-12"
        >
          <h3 className="text-xl font-bold text-orange-400 mb-2">
            Despliegue de Gel Retardante
          </h3>
          <p className="text-slate-300 text-sm max-w-xl mx-auto">
            Nuestros drones liberan gel retardante para frenar la propagación mientras llegan los equipos de emergencia.
          </p>
        </motion.div>

        {/* Partner Section - Dronivo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-slate-900 border border-slate-700 rounded-2xl p-6 md:p-8"
        >
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex-shrink-0 text-center">
              <div className="text-4xl mb-2">🇩🇪</div>
              <div className="text-xs text-slate-400">Partner Tecnológico</div>
            </div>
            <div className="flex-1 text-center md:text-left">
              <h3 className="text-xl font-bold text-white mb-2">
                Respaldados por <span className="text-blue-400">Dronivo</span> (Alemania)
              </h3>
              <p className="text-slate-400 text-sm mb-3">
                Expertos en drones para emergencias (BOS). Entrenan bomberos en Europa con DJI Mavic 3T.
              </p>
              <div className="flex flex-wrap gap-3 justify-center md:justify-start text-xs">
                <span className="px-3 py-1 bg-slate-800 rounded-full text-slate-300">+5 años experiencia</span>
                <span className="px-3 py-1 bg-slate-800 rounded-full text-slate-300">Certificación DJI</span>
                <span className="px-3 py-1 bg-slate-800 rounded-full text-slate-300">Training bomberos</span>
              </div>
            </div>
            <div className="flex-shrink-0">
              <a
                href="https://www.dronivo.de"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block px-4 py-2 border border-slate-600 hover:border-blue-400 rounded-lg text-sm text-slate-300 hover:text-blue-400 transition-colors"
              >
                Ver Partner →
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default ThermalShowcase;
