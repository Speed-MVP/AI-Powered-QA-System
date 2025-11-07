import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Test } from '@/pages/Test'
import { Home } from '@/pages/Home'
import { Upload } from '@/pages/Upload'
import { Dashboard } from '@/pages/Dashboard'
import { Results } from '@/pages/Results'
import { PolicyTemplates } from '@/pages/PolicyTemplates'
import { Pricing } from '@/pages/Pricing'
import { Features } from '@/pages/Features'
import { SignIn } from '@/pages/SignIn'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Test />} />
          <Route path="test" element={<Test />} />
          <Route path="home" element={<Home />} />
          <Route path="upload" element={<Upload />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="results" element={<Results />} />
          <Route path="policy-templates" element={<PolicyTemplates />} />
          <Route path="pricing" element={<Pricing />} />
          <Route path="features" element={<Features />} />
          <Route path="sign-in" element={<SignIn />} />
          <Route path="login" element={<SignIn />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
