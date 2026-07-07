import { useTranslation } from 'react-i18next'

export function Disclaimer() {
  const { t } = useTranslation()
  return (
    <p className="mx-auto max-w-2xl rounded-lg border border-edge bg-card-2 px-4 py-2.5 text-center text-xs text-ink-muted">
      ⚕ {t('common.disclaimer')}
    </p>
  )
}
