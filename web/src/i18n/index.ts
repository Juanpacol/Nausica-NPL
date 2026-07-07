import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import es from './es.json'
import en from './en.json'

const stored = localStorage.getItem('nausica-lang')

i18n.use(initReactI18next).init({
  resources: { es: { translation: es }, en: { translation: en } },
  lng: stored === 'en' || stored === 'es' ? stored : 'es', // Spanish default (jury)
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

i18n.on('languageChanged', (lng) => {
  localStorage.setItem('nausica-lang', lng)
  document.documentElement.lang = lng
})

export default i18n
