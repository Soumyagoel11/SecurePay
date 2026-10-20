import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'

import CustomerDashboard from './pages/customer/Dashboard'
import CustomerWallet from './pages/customer/Wallet'
import MakePayment from './pages/customer/MakePayment'
import CustomerTransactions from './pages/customer/Transactions'
import PaymentDetails from './pages/customer/PaymentDetails'
import RefundRequest from './pages/customer/RefundRequest'
import CustomerProfile from './pages/customer/Profile'

import MerchantDashboard from './pages/merchant/Dashboard'
import MerchantQRTerminal from './pages/merchant/QRTerminal'
import MerchantPayments from './pages/merchant/ReceivedPayments'
import MerchantTransactions from './pages/merchant/Transactions'
import MerchantSuspicious from './pages/merchant/Suspicious'
import MerchantProfile from './pages/merchant/Profile'
import QRPaymentCheckout from './pages/QRPaymentCheckout'

import AdminDashboard from './pages/admin/Dashboard'
import AdminUsers from './pages/admin/Users'
import AdminMerchants from './pages/admin/Merchants'
import AdminTransactions from './pages/admin/Transactions'
import AdminFraudReports from './pages/admin/FraudReports'
import AdminRefundManagement from './pages/admin/RefundManagement'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Public QR Code Checkout (scanned via Google Lens / Camera) */}
        <Route path="/pay/qr/:token" element={<QRPaymentCheckout />} />
        <Route path="/pay/merchant/:merchantId" element={<QRPaymentCheckout isStoreQR={true} />} />

        {/* Customer */}
        <Route path="/customer" element={<ProtectedRoute role="customer"><CustomerDashboard /></ProtectedRoute>} />
        <Route path="/customer/wallet" element={<ProtectedRoute role="customer"><CustomerWallet /></ProtectedRoute>} />
        <Route path="/customer/pay" element={<ProtectedRoute role="customer"><MakePayment /></ProtectedRoute>} />
        <Route path="/customer/transactions" element={<ProtectedRoute role="customer"><CustomerTransactions /></ProtectedRoute>} />
        <Route path="/customer/transactions/:id" element={<ProtectedRoute role="customer"><PaymentDetails /></ProtectedRoute>} />
        <Route path="/customer/refund" element={<ProtectedRoute role="customer"><RefundRequest /></ProtectedRoute>} />
        <Route path="/customer/profile" element={<ProtectedRoute role="customer"><CustomerProfile /></ProtectedRoute>} />

        {/* Merchant */}
        <Route path="/merchant" element={<ProtectedRoute role="merchant"><MerchantDashboard /></ProtectedRoute>} />
        <Route path="/merchant/qr-terminal" element={<ProtectedRoute role="merchant"><MerchantQRTerminal /></ProtectedRoute>} />
        <Route path="/merchant/payments" element={<ProtectedRoute role="merchant"><MerchantPayments /></ProtectedRoute>} />
        <Route path="/merchant/transactions" element={<ProtectedRoute role="merchant"><MerchantTransactions /></ProtectedRoute>} />
        <Route path="/merchant/suspicious" element={<ProtectedRoute role="merchant"><MerchantSuspicious /></ProtectedRoute>} />
        <Route path="/merchant/profile" element={<ProtectedRoute role="merchant"><MerchantProfile /></ProtectedRoute>} />

        {/* Admin */}
        <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute role="admin"><AdminUsers /></ProtectedRoute>} />
        <Route path="/admin/merchants" element={<ProtectedRoute role="admin"><AdminMerchants /></ProtectedRoute>} />
        <Route path="/admin/transactions" element={<ProtectedRoute role="admin"><AdminTransactions /></ProtectedRoute>} />
        <Route path="/admin/fraud" element={<ProtectedRoute role="admin"><AdminFraudReports /></ProtectedRoute>} />
        <Route path="/admin/refunds" element={<ProtectedRoute role="admin"><AdminRefundManagement /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
