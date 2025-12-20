"use client"
import { createContext, useContext, useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { usePathname } from "next/navigation"
import ProfileCompletionModal from "../components/Modals/ProfileCompletionModal"
import { locales } from "../../i18n/routing"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Pages where we don't show the profile completion modal
const EXCLUDED_PATHS = [
  "/login",
  "/register",
  "/verify",
  "/forgot-password",
  "/reset-password",
  "/termsandservices",
  "/privacy",
  "/report",
]

interface UserData {
  profile_completed: boolean
  provider: string
  name?: string
  avatar_url?: string | null
}

const UserProfileContext = createContext<UserData | null>(null)

export function useUserProfile() {
  return useContext(UserProfileContext)
}

interface ExtendedSession {
  accessToken?: string
  user?: {
    name?: string | null
    email?: string | null
    image?: string | null
  }
}

export default function ProfileCompletionWrapper({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const pathname = usePathname()
  const [showModal, setShowModal] = useState(false)
  const [userData, setUserData] = useState<UserData | null>(null)
  const [checked, setChecked] = useState(false)

  const normalizedPathname = (() => {
    const pattern = new RegExp(`^/(${locales.join("|")})(?=/|$)`)
    const stripped = pathname.replace(pattern, "")
    return stripped.length ? stripped : "/"
  })()

  useEffect(() => {
    const checkProfileCompletion = async () => {
      if (status !== "authenticated" || !session) {
        setChecked(true)
        return
      }

      // Don't check on excluded paths
      if (EXCLUDED_PATHS.some(path => normalizedPathname.startsWith(path))) {
        setChecked(true)
        return
      }

      const extendedSession = session as unknown as ExtendedSession
      const accessToken = extendedSession.accessToken
      if (!accessToken) {
        setChecked(true)
        return
      }

      try {
        const response = await fetch(`${API_URL}/users/me`, {
          headers: {
            Authorization: `Bearer ${accessToken}`
          }
        })

        if (response.ok) {
          const data: UserData = await response.json()
          setUserData(data)

          if (!data.profile_completed && data.provider !== "system" && data.provider !== "deleted") {
            setShowModal(true)
          }
        }
      } catch (error) {
        console.error("Error checking profile completion:", error)
      } finally {
        setChecked(true)
      }
    }

    checkProfileCompletion()
  }, [session, status, pathname, normalizedPathname])

  const handleProfileComplete = () => {
    setShowModal(false)
    setUserData(prev => (prev ? { ...prev, profile_completed: true } : prev))
    // Optionally refresh the page or update local state
    window.location.reload()
  }

  const handleProfileDismiss = () => {
    setShowModal(false)
    setUserData(prev => (prev ? { ...prev, profile_completed: true } : prev))
  }

  // Don't render anything until we've checked
  if (status === "loading" || !checked) {
    return <>{children}</>
  }

  const extendedSession = session as unknown as ExtendedSession

  return (
    <UserProfileContext.Provider value={userData}>
      {children}
      {session && (
        <ProfileCompletionModal
          open={showModal}
          accessToken={extendedSession?.accessToken || ""}
          userName={userData?.name}
          onComplete={handleProfileComplete}
          onClose={handleProfileDismiss}
        />
      )}
    </UserProfileContext.Provider>
  )
}
