# FireWatch Chile — Landing Page

Sistema de detección de incendios forestales con drones. Landing page premium construida con React, Vite y Tailwind CSS.

## Stack

- **React 18** + **Vite 5** — framework y bundler
- **Tailwind CSS 3** — estilos utilitarios
- **Framer Motion** — animaciones
- **Lucide React** — íconos
- **React Hook Form** — formularios

## Comandos

```bash
npm run dev       # servidor de desarrollo (localhost:5173)
npm run build     # build de producción
npm run preview   # preview del build
npm run lint      # lint con ESLint
```

## Estructura

```
src/
  App.jsx                 # componente raíz, orquesta secciones
  main.jsx                # punto de entrada
  index.css               # estilos globales + Tailwind
  components/
    Navbar.jsx
    Hero.jsx
    ProblemSection.jsx
    SolutionSection.jsx
    TechnologySection.jsx
    ThermalShowcase.jsx
    DJIInterface.jsx
    ProcessSection.jsx
    VisualWorkflow.jsx
    UseCases.jsx
    WhyNow.jsx
    FAQ.jsx
    Contact.jsx
    Footer.jsx
```

## Convenciones

- Componentes en PascalCase, archivos `.jsx`
- Estilos con clases Tailwind inline (no CSS módulos)
- Animaciones con Framer Motion (`motion.*` + variantes)
- Íconos de `lucide-react`
- No hay router — es una single page con scroll
- Imágenes en `src/` junto a los componentes

## Notas

- El tema visual es oscuro (dark mode por defecto), con tonos naranja/rojo para fuego
- Hay versiones alternativas del HTML en la raíz (`firewatch-IMPROVED.html`, `firewatch-preview.html`) — son prototipos estáticos, la fuente de verdad es `src/`
