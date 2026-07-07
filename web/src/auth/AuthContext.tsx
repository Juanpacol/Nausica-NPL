import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { loginUser, registerUser } from '../api/client'

interface AuthState {
  token: string | null
  userId: string | null
  email: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState>({
  token: null,
  userId: null,
  email: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
})

function clearStorage() {
  localStorage.removeItem('nausica_token')
  localStorage.removeItem('nausica_user_id')
  localStorage.removeItem('nausica_email')
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('nausica_token'))
  const [userId, setUserId] = useState<string | null>(() =>
    localStorage.getItem('nausica_user_id'),
  )
  const [email, setEmail] = useState<string | null>(() => localStorage.getItem('nausica_email'))

  const persist = useCallback((accessToken: string, id: string, mail: string) => {
    localStorage.setItem('nausica_token', accessToken)
    localStorage.setItem('nausica_user_id', id)
    localStorage.setItem('nausica_email', mail)
    setToken(accessToken)
    setUserId(id)
    setEmail(mail)
  }, [])

  const login = useCallback(
    async (mail: string, password: string) => {
      const res = await loginUser(mail, password)
      persist(res.access_token, res.user_id, mail)
    },
    [persist],
  )

  const register = useCallback(
    async (mail: string, password: string) => {
      const res = await registerUser(mail, password)
      persist(res.access_token, res.user_id, mail)
    },
    [persist],
  )

  const logout = useCallback(() => {
    clearStorage()
    setToken(null)
    setUserId(null)
    setEmail(null)
  }, [])

  useEffect(() => {
    const onUnauthorized = () => logout()
    window.addEventListener('nausica:unauthorized', onUnauthorized)
    return () => window.removeEventListener('nausica:unauthorized', onUnauthorized)
  }, [logout])

  return (
    <AuthContext.Provider value={{ token, userId, email, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
