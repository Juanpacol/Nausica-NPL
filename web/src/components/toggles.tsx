import { useTranslation } from 'react-i18next'
import { useTheme } from '../theme/ThemeProvider'

export function LangToggle() {
  const { i18n } = useTranslation()
  const next = i18n.language === 'es' ? 'en' : 'es'
  return (
    <button
      onClick={() => i18n.changeLanguage(next)}
      className="rounded-full border border-edge px-3 py-1 text-sm font-medium text-ink hover:bg-card-2"
      aria-label={`Switch language to ${next.toUpperCase()}`}
    >
      {i18n.language === 'es' ? 'EN' : 'ES'}
    </button>
  )
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const { t } = useTranslation()
  return (
    <button
      onClick={toggle}
      className="rounded-full border border-edge px-3 py-1 text-sm text-ink hover:bg-card-2"
      aria-label={theme === 'light' ? t('nav.themeDark') : t('nav.themeLight')}
      title={theme === 'light' ? t('nav.themeDark') : t('nav.themeLight')}
    >
      {theme === 'light' ? '☾' : '☀'}
    </button>
  )
}
