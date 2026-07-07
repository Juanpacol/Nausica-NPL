import { NavLink, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Landing } from './views/Landing'
import { Analyze } from './views/Analyze'
import { Reframe } from './views/Reframe'
import { LangToggle, ThemeToggle } from './components/toggles'

function App() {
  const { t } = useTranslation()

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
      isActive ? 'bg-brand text-white' : 'text-ink hover:bg-card-2'
    }`

  return (
    <div className="min-h-screen bg-canvas">
      <nav className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-edge bg-card/80 px-6 backdrop-blur">
        <NavLink to="/" className="text-lg font-bold tracking-tight text-brand">
          Nausica
        </NavLink>
        <div className="flex items-center gap-2">
          <NavLink to="/" end className={linkClass}>
            {t('nav.home')}
          </NavLink>
          <NavLink to="/analyze" className={linkClass}>
            {t('nav.analyze')}
          </NavLink>
          <NavLink to="/reframe" className={linkClass}>
            {t('nav.reframe')}
          </NavLink>
          <span className="mx-1 h-5 w-px bg-edge" aria-hidden="true" />
          <LangToggle />
          <ThemeToggle />
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/reframe" element={<Reframe />} />
      </Routes>
    </div>
  )
}

export default App
