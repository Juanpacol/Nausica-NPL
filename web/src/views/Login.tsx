import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Disclaimer } from '../components/Disclaimer'

type Mode = 'login' | 'register'

export function Login() {
  const { t } = useTranslation()
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (loading) return
    setLoading(true)
    setError(null)
    try {
      if (mode === 'login') await login(email.trim(), password)
      else await register(email.trim(), password)
      const from = (location.state as { from?: string } | null)?.from ?? '/analyze'
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : t('auth.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="mx-auto max-w-md">
        <header className="mb-8 text-center">
          <h1 className="mb-2 text-3xl font-bold text-ink">
            {mode === 'login' ? t('auth.login') : t('auth.register')}
          </h1>
        </header>

        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-edge bg-card p-6 shadow-sm"
        >
          <label className="mb-1 block text-sm font-medium text-ink" htmlFor="auth-email">
            {t('auth.email')}
          </label>
          <input
            id="auth-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mb-4 w-full rounded-xl border border-edge bg-card p-3 text-ink shadow-sm outline-none placeholder:text-ink-muted focus:border-brand-2"
            placeholder="you@example.com"
          />

          <label className="mb-1 block text-sm font-medium text-ink" htmlFor="auth-password">
            {t('auth.password')}
          </label>
          <input
            id="auth-password"
            type="password"
            required
            minLength={mode === 'register' ? 8 : undefined}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-6 w-full rounded-xl border border-edge bg-card p-3 text-ink shadow-sm outline-none placeholder:text-ink-muted focus:border-brand-2"
          />

          {error && (
            <p className="mb-4 rounded-xl border border-edge bg-card-2 p-3 text-center text-sm text-ink">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-cta px-6 py-2.5 font-semibold text-white shadow-md hover:opacity-90 disabled:opacity-40"
          >
            {loading
              ? t('auth.submitting')
              : mode === 'login'
                ? t('auth.submitLogin')
                : t('auth.submitRegister')}
          </button>

          <button
            type="button"
            onClick={() => {
              setMode((m) => (m === 'login' ? 'register' : 'login'))
              setError(null)
            }}
            className="mt-4 w-full text-center text-sm text-ink-muted hover:text-ink"
          >
            {mode === 'login' ? t('auth.switchToRegister') : t('auth.switchToLogin')}
          </button>
        </form>

        <div className="mt-8">
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}
