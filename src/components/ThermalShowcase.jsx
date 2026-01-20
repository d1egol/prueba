import { motion } from 'framer-motion';

const ThermalShowcase = () => {
  const services = [
    {
      src: '/images/thermal-forest.jpg',
      title: 'Detección Térmica',
      desc: 'Identificamos focos de calor antes de que sean visibles',
    },
    {
      src: '/images/dji-interface.png',
      title: 'Monitoreo 24/7',
      desc: 'Control en tiempo real con interface profesional DJI',
    },
    {
      src: '/images/mapa-incendios.png',
      title: 'Mapa de Incendios',
      desc: 'Visualización de zonas de riesgo en tiempo real',
    },
  ];

  return (
    <section id="servicios" className="bg-slate-950 py-20">
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Nuestros <span className="text-orange-500">Servicios</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Tecnología de punta para proteger bosques y comunidades
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
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

        {/* Gel Retardante - Feature destacado */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-12 bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-2xl p-8 text-center"
        >
          <h3 className="text-2xl font-bold text-orange-400 mb-3">
            Despliegue de Gel Retardante
          </h3>
          <p className="text-slate-300 max-w-2xl mx-auto">
            Nuestros drones pueden liberar gel retardante para frenar la propagación del fuego
            mientras llegan los equipos de emergencia.
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default ThermalShowcase;
