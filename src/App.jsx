import { useState } from 'react'
import Hero from './components/Hero'
import ThermalShowcase from './components/ThermalShowcase'
import ProblemSection from './components/ProblemSection'
import SolutionSection from './components/SolutionSection'
import VisualWorkflow from './components/VisualWorkflow'
import ProcessSection from './components/ProcessSection'
import DJIInterface from './components/DJIInterface'
import TechnologySection from './components/TechnologySection'
import UseCases from './components/UseCases'
import WhyNow from './components/WhyNow'
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
      <ProblemSection />
      <SolutionSection />
      <VisualWorkflow />
      <ProcessSection />
      <DJIInterface />
      <TechnologySection />
      <UseCases />
      <WhyNow />
      <FAQ />
      <Contact />
      <Footer />
    </div>
  )
}

export default App
