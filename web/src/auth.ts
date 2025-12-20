import NextAuth from "next-auth"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"
import axios from "axios"

const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type BackendTokenResponse = {
  access_token: string
  refresh_token: string
  expires_in: number
}

type BackendUser = {
  id: string
  avatar_url?: string | null
}

type ConsentResponse = {
  status: string
  data: {
    id: number
    version: string
  } | null
  message?: string
}

/**
 * Fetches the authenticated user's profile from the backend.
 *
 * @param accessToken - Bearer access token used for Authorization header
 * @returns The user's profile data as a `BackendUser`
 */
async function fetchUserProfile(accessToken: string): Promise<BackendUser> {
  const userRes = await axios.get(`${apiUrl}/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` }
  })
  return userRes.data
}

/**
 * Refreshes an access token using the stored refresh token and returns an updated token object.
 *
 * @param token - Token-like object that must include a `refreshToken` string; other token fields are preserved.
 * @returns An updated token object containing `accessToken`, `refreshToken` (backend value or original if not returned), `accessTokenExpires` (epoch ms), and `error: undefined` on success; on failure returns the original token with `error` set to `"RefreshAccessTokenError"`.
 */
async function refreshAccessToken(token: Record<string, unknown>) {
  try {
    const refreshToken = token.refreshToken as string | undefined
    if (!refreshToken) {
      throw new Error("Missing refresh token")
    }
    const res = await axios.post<BackendTokenResponse>(`${apiUrl}/auth/refresh`, {
      refresh_token: refreshToken
    })
    return {
      ...token,
      accessToken: res.data.access_token,
      refreshToken: res.data.refresh_token ?? refreshToken,
      accessTokenExpires: Date.now() + res.data.expires_in * 1000,
      error: undefined
    }
  } catch (error) {
    console.error("Refresh token error", error)
    return { ...token, error: "RefreshAccessTokenError" }
  }
}

/**
 * Fetches the latest consent version ID from the backend.
 *
 * @returns The latest consent ID as a number.
 * @throws Error if the backend response does not include a consent ID
 */
async function fetchLatestConsentId(): Promise<number> {
  const res = await axios.get<ConsentResponse>(`${apiUrl}/consents/latest`)
  const consentId = res.data.data?.id
  if (!consentId) {
    throw new Error("Consent version not configured")
  }
  return consentId
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
  trustHost: true,  // Required for reverse proxy (nginx/Cloudflare)
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    Credentials({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        const email = credentials?.email
        const password = credentials?.password

        if (typeof email !== "string" || typeof password !== "string") {
          return null
        }
        try {
          const formData = new URLSearchParams()
          formData.append("username", email)
          formData.append("password", password)

          const res = await axios.post<BackendTokenResponse>(`${apiUrl}/auth/login`, formData, {
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
          })

          const userProfile = await fetchUserProfile(res.data.access_token)

          return {
            ...userProfile,
            accessToken: res.data.access_token,
            refreshToken: res.data.refresh_token,
            accessTokenExpiresIn: res.data.expires_in
          }
        } catch (error) {
          console.error("Credentials auth error", error)
          return null
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      if (account?.provider === "google" && account.id_token) {
        try {
          const consentId = await fetchLatestConsentId()
          const res = await axios.post<BackendTokenResponse>(`${apiUrl}/auth/google`, {
            token: account.id_token,
            consent_id: consentId,
          })
          const profile = await fetchUserProfile(res.data.access_token)
          return {
            ...token,
            accessToken: res.data.access_token,
            refreshToken: res.data.refresh_token,
            accessTokenExpires: Date.now() + res.data.expires_in * 1000,
            id: profile.id,
            picture: profile.avatar_url,
            error: undefined
          }
        } catch (e) {
          console.error("Google auth error", e)
          return { ...token, error: "GoogleAuthError" }
        }
      }

      if (user) {
        return {
          ...token,
          accessToken: (user as { accessToken?: string }).accessToken,
          refreshToken: (user as { refreshToken?: string }).refreshToken,
          accessTokenExpires: Date.now() + ((user as { accessTokenExpiresIn?: number }).accessTokenExpiresIn ?? 0) * 1000,
          id: (user as { id?: string }).id ?? token.id,
          picture: (user as { avatar_url?: string }).avatar_url ?? token.picture,
          error: undefined
        }
      }

      const accessTokenExpires = token.accessTokenExpires as number | undefined
      if (!accessTokenExpires || Date.now() < accessTokenExpires - 30_000) {
        return token
      }

      return refreshAccessToken(token)
    },
    async session({ session, token }) {
      (session as { accessToken?: string }).accessToken = token.accessToken as string
      ;(session as { error?: string }).error = token.error as string | undefined
      if (session.user) {
          (session.user as { id?: string }).id = token.id as string
          session.user.image = token.picture as string
      }
      return session
    },
  },
  pages: {
    signIn: '/login',
  }
})