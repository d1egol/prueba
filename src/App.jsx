import Hero from './components/Hero'
import ThermalShowcase from './components/ThermalShowcase'
import FAQ from './components/FAQ'
import Contact from './components/Contact'
import Footer from './components/Footer'
import Navbar from './components/Navbar'

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <Navbar />
      <Hero />
      <ThermalShowcase />
      <FAQ />
      <Contact />
      <Footer />
    </div>
  )
}

export default App
