import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { ReactNode } from 'react'
import { Landing } from './views/Landing'
import { Analyze } from './views/Analyze'
import { Reframe } from './views/Reframe'
import { Login } from './views/Login'
import { ClinicianDashboard } from './views/ClinicianDashboard'
import { LangToggle, ThemeToggle } from './components/toggles'
import { useAuth } from './auth/AuthContext'

function RequireAuth({ children }: { children: ReactNode }) {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}

function App() {
  const { t } = useTranslation()
  const { token, email, logout } = useAuth()
  const navigate = useNavigate()

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
          {token && (
            <NavLink to="/dashboard" className={linkClass}>
              {t('nav.dashboard')}
            </NavLink>
          )}
          <span className="mx-1 h-5 w-px bg-edge" aria-hidden="true" />
          {token ? (
            <>
              <span className="hidden text-sm text-ink-muted sm:inline">{email}</span>
              <button
                onClick={() => {
                  logout()
                  navigate('/')
                }}
                className="rounded-full border border-edge px-3 py-1 text-sm text-ink hover:bg-card-2"
              >
                {t('auth.logout')}
              </button>
            </>
          ) : (
            <NavLink to="/login" className={linkClass}>
              {t('auth.login')}
            </NavLink>
          )}
          <LangToggle />
          <ThemeToggle />
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/analyze"
          element={
            <RequireAuth>
              <Analyze />
            </RequireAuth>
          }
        />
        <Route
          path="/reframe"
          element={
            <RequireAuth>
              <Reframe />
            </RequireAuth>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <ClinicianDashboard />
            </RequireAuth>
          }
        />
      </Routes>
    </div>
  )
}

export default App
