import { motion } from 'framer-motion';
import { useState } from 'react';

const ThermalShowcase = () => {
  const [activePalette, setActivePalette] = useState('rainbow');

  const palettes = [
    { id: 'rainbow', label: '🌈 Rainbow', description: 'Alta sensibilidad térmica' },
    { id: 'ironbow', label: '🔥 Ironbow', description: 'Contraste optimizado' },
    { id: 'arctic', label: '❄️ Arctic', description: 'Operación 24/7' },
    { id: 'blackhot', label: '⚫ Blackhot', description: 'Visión nocturna' },
    { id: 'whitehot', label: '⚪ Whitehot', description: 'Alto contraste' },
    { id: 'fulgurite', label: '🎨 Fulgurite', description: 'Análisis detallado' },
    { id: 'hotmetal', label: '💎 Hotmetal', description: 'Puntos extremos' },
  ];

  const thermalImages = [
    {
      src: 'https://images.unsplash.com/photo-1473445730015-841f29a9490b?w=800&q=80',
      label: '🔥 Rainbow Palette',
      description: 'Alta sensibilidad térmica',
    },
    {
      src: 'https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=800&q=80',
      label: '🌡️ Ironbow Palette',
      description: 'Contraste optimizado',
    },
    {
      src: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&q=80',
      label: '❄️ Arctic Palette',
      description: 'Operación 24/7',
    },
  ];

  return (
    <section className="bg-gradient-to-b from-slate-950 to-slate-900 py-24">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <span className="text-orange-500 uppercase text-sm font-bold tracking-wider">
            Tecnología de Detección
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mt-4 mb-6">
            Visión térmica que{' '}
            <span className="bg-gradient-to-r from-orange-400 to-green-400 bg-clip-text text-transparent">
              salva vidas
            </span>
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Detectamos incendios antes de que sean visibles al ojo humano usando cámaras térmicas de
            última generación
          </p>
        </motion.div>

        {/* Thermal Gallery */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {thermalImages.map((image, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group relative rounded-xl overflow-hidden border-2 border-slate-800 hover:border-orange-500 transition-all duration-300 cursor-pointer hover:scale-105 aspect-video bg-slate-900"
            >
              <img
                src={image.src}
                alt={image.label}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black to-transparent">
                <div className="font-semibold text-orange-400 text-sm uppercase tracking-wide">
                  {image.label}
                </div>
                <p className="text-slate-300 text-xs mt-1">{image.description}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Comparison Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h3 className="text-2xl font-bold text-center text-blue-400 mb-8">
            Comparación: Visión Normal vs Térmica
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="relative rounded-xl overflow-hidden border-2 border-slate-700 aspect-video">
              <img
                src="https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?w=800&q=80"
                alt="Vista normal"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-4 left-4 px-4 py-2 bg-black/80 backdrop-blur-sm rounded-lg text-sm font-semibold">
                📷 Cámara Normal
              </div>
            </div>
            <div className="relative rounded-xl overflow-hidden border-2 border-orange-500 aspect-video">
              <img
                src="https://images.unsplash.com/photo-1526080652727-5b77f74eacd2?w=800&q=80"
                alt="Vista térmica"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-4 left-4 px-4 py-2 bg-black/80 backdrop-blur-sm rounded-lg text-sm font-semibold text-orange-400">
                🌡️ Cámara Térmica
              </div>
            </div>
          </div>
        </motion.div>

        {/* Description */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center mb-8"
        >
          <p className="text-lg leading-relaxed text-slate-300">
            La cámara térmica detecta diferencias de temperatura de hasta{' '}
            <strong className="text-orange-500">0.1°C</strong>, revelando focos de incendio{' '}
            <strong className="text-orange-500">hasta 2 horas antes</strong> de que sean visibles
            al ojo humano.
          </p>
        </motion.div>

        {/* Palette Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex flex-wrap justify-center gap-3"
        >
          {palettes.map((palette) => (
            <button
              key={palette.id}
              onClick={() => setActivePalette(palette.id)}
              className={`px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all duration-200 ${
                activePalette === palette.id
                  ? 'border-orange-500 bg-orange-500/10 text-orange-400'
                  : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-orange-500 hover:bg-orange-500/5'
              }`}
            >
              {palette.label}
            </button>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default ThermalShowcase;
