import { useState } from 'react';
import { motion } from 'framer-motion';

const Contact = () => {
  const [formData, setFormData] = useState({ nombre: '', email: '', mensaje: '' });
  const [enviado, setEnviado] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Formulario enviado:', formData);
    setEnviado(true);
  };

  return (
    <section id="contacto" className="bg-slate-950 py-20">
      <div className="container mx-auto px-4 max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-10"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            ¿Listo para <span className="text-orange-500">proteger tu zona</span>?
          </h2>
          <p className="text-slate-400">
            Contáctanos y te responderemos en menos de 24 horas
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6 md:p-8"
        >
          {enviado ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">✓</div>
              <h3 className="text-xl font-bold text-green-400 mb-2">Mensaje enviado</h3>
              <p className="text-slate-400">Te contactaremos pronto.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <input
                  type="text"
                  required
                  placeholder="Tu nombre"
                  value={formData.nombre}
                  onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <input
                  type="email"
                  required
                  placeholder="Tu email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <textarea
                  rows={3}
                  placeholder="¿Qué necesitas? (opcional)"
                  value={formData.mensaje}
                  onChange={(e) => setFormData({...formData, mensaje: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 resize-none"
                />
              </div>
              <button
                type="submit"
                className="w-full py-4 bg-orange-500 hover:bg-orange-600 rounded-lg font-bold text-lg transition-all"
              >
                Enviar Mensaje
              </button>
            </form>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-8 flex flex-wrap justify-center gap-6 text-slate-400 text-sm"
        >
          <span>contacto@dronewatch.cl</span>
          <span>•</span>
          <span>San Antonio, Chile</span>
        </motion.div>
      </div>
    </section>
  );
};

export default Contact;
