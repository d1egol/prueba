import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const faqs = [
  {
    question: '¿Cuánto cuesta el servicio?',
    answer: 'Planes personalizados según el área. Agenda reunión para cotización sin compromiso.'
  },
  {
    question: '¿Funciona de noche y con mal clima?',
    answer: 'Sí. Las cámaras térmicas operan 24/7 en cualquier condición. Los drones soportan vientos de hasta 40 km/h.'
  },
  {
    question: '¿Qué área pueden cubrir?',
    answer: 'Un dron cubre hasta 500 hectáreas por vuelo. Con una flota de 3-5 drones cubrimos hasta 10,000 hectáreas en monitoreo continuo.'
  },
  {
    question: '¿Cómo funciona el gel retardante?',
    answer: 'Los drones liberan gel retardante sobre el foco del incendio para frenar su propagación mientras llegan los equipos de emergencia.'
  }
];

const FAQ = () => {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section id="faq" className="bg-slate-900 py-20">
      <div className="container mx-auto px-4 max-w-3xl">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-3xl font-bold text-center mb-10"
        >
          Preguntas <span className="text-orange-500">Frecuentes</span>
        </motion.h2>

        <div className="space-y-3">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05 }}
              className="border border-slate-700 rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? -1 : index)}
                className="w-full p-4 flex justify-between items-center text-left hover:bg-slate-800/50 transition-colors"
              >
                <span className="font-medium">{faq.question}</span>
                <span className={`text-orange-500 transition-transform ${openIndex === index ? 'rotate-180' : ''}`}>
                  ▼
                </span>
              </button>
              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <p className="p-4 pt-0 text-slate-400">{faq.answer}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQ;
