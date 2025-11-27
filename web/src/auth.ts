import NextAuth from "next-auth"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"
import axios from "axios"

export const { handlers, signIn, signOut, auth } = NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
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
        const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        try {
          const res = await axios.post(`${apiUrl}/auth/login`, {
            username: credentials.email,
            password: credentials.password,
          }, {
             headers: { "Content-Type": "application/x-www-form-urlencoded" }
          })
          
          if (res.data && res.data.access_token) {
             const userRes = await axios.get(`${apiUrl}/users/me`, {
                headers: { Authorization: `Bearer ${res.data.access_token}` }
             })
             return { ...userRes.data, accessToken: res.data.access_token }
          }
          return null
        } catch {
          return null
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      if (user) {
        token.accessToken = (user as { accessToken?: string }).accessToken
        token.id = (user as { id?: string }).id
      }
      if (account?.provider === "google") {
        try {
           const res = await axios.post(`${apiUrl}/auth/google`, {
             token: account.id_token
           })
           if (res.data && res.data.access_token) {
             token.accessToken = res.data.access_token
             // Fetch user details from backend to get ID
             const userRes = await axios.get(`${apiUrl}/users/me`, {
                headers: { Authorization: `Bearer ${res.data.access_token}` }
             })
             token.id = userRes.data.id
             token.picture = userRes.data.avatar_url
           }
        } catch (e) {
          console.error("Google auth error", e)
        }
      }
      return token
    },
    async session({ session, token }) {
      (session as { accessToken?: string }).accessToken = token.accessToken as string
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
