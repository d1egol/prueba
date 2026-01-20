import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const faqs = [
  {
    question: '¿Cuál es el costo de implementación?',
    answer: 'El costo depende del área a monitorear y la configuración específica. Ofrecemos un diagnóstico gratuito donde evaluamos tus necesidades y entregamos una propuesta detallada. Nuestros clientes típicamente ven ROI positivo en 12-18 meses considerando la reducción de pérdidas por incendios.'
  },
  {
    question: '¿Cuánto tiempo toma la implementación completa?',
    answer: 'Una implementación típica toma entre 4-8 semanas, dependiendo del alcance. Esto incluye: instalación de estaciones de monitoreo, configuración de drones, integración con sistemas existentes, y capacitación de tu equipo. Ofrecemos implementación por fases para minimizar riesgos.'
  },
  {
    question: '¿Funciona en condiciones climáticas adversas?',
    answer: 'Sí. Nuestras cámaras térmicas funcionan 24/7, incluso en condiciones de humo, niebla o lluvia ligera. Los drones tienen clasificación IP54 y pueden operar con vientos de hasta 40 km/h. En condiciones extremas, el sistema activa protocolos de respaldo con estaciones fijas.'
  },
  {
    question: '¿Qué pasa si un dron falla durante una emergencia?',
    answer: 'El sistema está diseñado con redundancia. Cada zona crítica es cubierta por múltiples sensores y drones. Si un dron falla, otro toma su lugar automáticamente. Además, todos los datos se transmiten en tiempo real, por lo que la información nunca se pierde.'
  },
  {
    question: '¿Cómo se integra con los sistemas de emergencia existentes?',
    answer: 'PyroGuard se integra mediante APIs estándar con sistemas CONAF, centrales de bomberos, y plataformas municipales de emergencia. Podemos enviar alertas directas a WhatsApp, email, SMS, o sistemas de comando ya existentes. La integración típica toma 1-2 semanas.'
  },
  {
    question: '¿Qué área puede monitorear el sistema?',
    answer: 'Un solo dron puede monitorear hasta 500 hectáreas por vuelo. Con una flota de 3-5 drones y estaciones de carga automática, cubrimos fácilmente 5,000-10,000 hectáreas con patrullaje continuo 24/7. Para áreas mayores, diseñamos soluciones escalables.'
  },
  {
    question: '¿Necesitamos personal técnico especializado?',
    answer: 'No. El sistema es autónomo y fácil de operar. Incluimos capacitación completa para tu equipo (típicamente 2 días). El monitoreo puede hacerse desde cualquier computador o tablet. Ofrecemos soporte técnico 24/7 y actualizaciones automáticas del software.'
  },
  {
    question: '¿Cómo manejan los falsos positivos?',
    answer: 'Nuestra IA ha sido entrenada con miles de imágenes térmicas de Chile y reduce los falsos positivos en un 94% comparado con sistemas tradicionales. Cuando hay duda, el sistema envía un dron de verificación antes de activar la alerta general, evitando movilizaciones innecesarias.'
  }
];

const FAQItem = ({ faq, isOpen, onToggle }) => {
  return (
    <div className="border-b border-slate-800 last:border-0">
      <button
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-label={`${isOpen ? 'Cerrar' : 'Abrir'} pregunta: ${faq.question}`}
        className="w-full py-6 flex items-center justify-between text-left hover:text-orange-400 transition-colors focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-slate-900 rounded-lg"
      >
        <span className="text-lg font-medium pr-8">{faq.question}</span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="flex-shrink-0"
        >
          <svg
            className="w-5 h-5 text-orange-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <p className="pb-6 text-slate-300 leading-relaxed">
              {faq.answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const FAQ = () => {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section id="faq" className="bg-gradient-to-b from-slate-950 to-slate-900 py-24">
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <span className="text-orange-500 uppercase text-sm font-bold tracking-wider">Preguntas Frecuentes</span>
          <h2 className="text-4xl md:text-5xl font-bold mt-4">
            Lo que probablemente{' '}
            <span className="text-blue-400">te estás preguntando</span>
          </h2>
          <p className="text-xl text-slate-300 mt-6">
            Respuestas directas a las preguntas más comunes sobre PyroGuard.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="bg-slate-900/50 border border-slate-800 rounded-2xl px-6 md:px-8"
        >
          {faqs.map((faq, index) => (
            <FAQItem
              key={index}
              faq={faq}
              isOpen={openIndex === index}
              onToggle={() => setOpenIndex(openIndex === index ? -1 : index)}
            />
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-slate-400 mb-4">
            ¿Tienes otra pregunta que no está aquí?
          </p>
          <a
            href="#contacto"
            className="inline-flex items-center gap-2 text-orange-400 hover:text-orange-300 font-medium transition-colors"
            aria-label="Ir a la sección de contacto para hacer una pregunta"
          >
            Contáctanos directamente
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </a>
        </motion.div>
      </div>
    </section>
  );
};

export default FAQ;
