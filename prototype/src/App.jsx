import React, { useState } from 'react';
import { evaluateSafeVault } from './rules';
import { verifyHold } from './verification';
import { Shield, Phone, AlertTriangle, CheckCircle, Clock, ShieldAlert, HeartPulse } from 'lucide-react';

function App() {
  // Transaction State
  const [amount, setAmount] = useState(5000);
  const [payee, setPayee] = useState('known_individual'); // known_individual, new_individual, new_merchant, family, hospital
  const [account, setAccount] = useState('everyday'); // everyday, vault
  const [channel, setChannel] = useState('UPI'); // UPI, RTGS

  // Context State
  const [onCall, setOnCall] = useState(false);
  const [isCallFlagged, setIsCallFlagged] = useState(false);
  const [age, setAge] = useState(72);
  const [fdJustBroken, setFdJustBroken] = useState(false);
  const [velocity24h, setVelocity24h] = useState(1);

  // Results State
  const [decision, setDecision] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [trustedPersonResponse, setTrustedPersonResponse] = useState(null);

  const handlePay = async () => {
    setDecision(null);
    setVerificationResult(null);
    setTrustedPersonResponse(null);

    // Build tx object
    const tx = {
      amount: Number(amount),
      account,
      channel,
      isNewPayee: payee.startsWith('new_'),
      payeeType: payee.includes('merchant') ? 'merchant' : 'individual',
    };

    // Build context
    const isEmergency = payee === 'family' || payee === 'hospital' || payee === 'unlisted_emergency';
    const payeePreapproved = payee === 'family' || payee === 'hospital';

    const ctx = {
      onCall,
      isCallFlagged,
      age,
      fdJustBroken,
      velocity24h,
      isEmergency,
      payeePreapproved
    };

    const res = evaluateSafeVault(tx, ctx);
    setDecision(res);

    if (res.action === 'HOLD' && !isEmergency) {
      setIsVerifying(true);
      const vRes = await verifyHold({ tx, ctx });
      setVerificationResult(vRes);
      setIsVerifying(false);
    }
  };

  // Scenarios
  const setScenario = (type) => {
    switch (type) {
      case 'normal':
        setAmount(12000);
        setPayee('known_individual');
        setAccount('everyday');
        setChannel('UPI');
        setOnCall(false);
        setIsCallFlagged(false);
        setFdJustBroken(false);
        break;
      case 'digital_arrest':
        setAmount(1500000);
        setPayee('new_individual');
        setAccount('everyday');
        setChannel('RTGS');
        setOnCall(true);
        setIsCallFlagged(true);
        setFdJustBroken(false);
        break;
      case 'fd_break':
        setAmount(200000);
        setPayee('new_individual');
        setAccount('everyday');
        setChannel('RTGS');
        setOnCall(false);
        setIsCallFlagged(false);
        setFdJustBroken(true);
        break;
      case 'emergency':
        setAmount(85000);
        setPayee('unlisted_emergency');
        setAccount('everyday');
        setChannel('RTGS');
        setOnCall(false);
        setIsCallFlagged(false);
        setFdJustBroken(false);
        break;
    }
    setDecision(null);
    setVerificationResult(null);
    setTrustedPersonResponse(null);
  };

  return (
    <div className="min-h-screen bg-gray-100 font-sans pb-20">
      {/* Header */}
      <header className="bg-blue-900 text-white p-4 shadow-md flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-blue-300" />
          <h1 className="text-xl font-bold">SecureBank</h1>
        </div>
        <div className="text-sm bg-blue-800 px-3 py-1 rounded-full border border-blue-700 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-green-400" /> SafeVault Active
        </div>
      </header>

      <main className="max-w-5xl mx-auto mt-8 grid grid-cols-1 md:grid-cols-2 gap-8 px-4">
        
        {/* Left Col: App Interface */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">Transfer Money</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Amount (₹)</label>
                <input 
                  type="number" 
                  value={amount} 
                  onChange={e => setAmount(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-3 text-lg font-medium focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Payee</label>
                <select 
                  value={payee} 
                  onChange={e => setPayee(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-3 bg-white"
                >
                  <option value="known_individual">Ramesh (Known Individual)</option>
                  <option value="new_individual">Unknown Number (New Individual)</option>
                  <option value="new_merchant">Amazon (New Merchant)</option>
                  <option value="family">Son - Rahul (Pre-approved Family)</option>
                  <option value="hospital">City Hospital (Pre-approved Hospital)</option>
                  <option value="unlisted_emergency">Unlisted Doctor (Emergency)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">From Account</label>
                  <select 
                    value={account} 
                    onChange={e => setAccount(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg p-3 bg-white"
                  >
                    <option value="everyday">Everyday (Bal: ₹4,50,000)</option>
                    <option value="vault">Vault (Bal: ₹25,00,000)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Channel</label>
                  <select 
                    value={channel} 
                    onChange={e => setChannel(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg p-3 bg-white"
                  >
                    <option value="UPI">UPI (Fast)</option>
                    <option value="RTGS">RTGS (Large)</option>
                  </select>
                </div>
              </div>

              <button 
                onClick={handlePay}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-lg py-4 rounded-xl mt-4 transition-colors shadow-md"
              >
                Pay Securely
              </button>
            </div>
          </div>

          {/* Context Toggles (Simulation Controls) */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Device & Context Signals (Hidden)</h3>
            
            <div className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center gap-3">
                  <Phone className={`w-5 h-5 ${onCall ? 'text-red-500' : 'text-gray-400'}`} />
                  <span className="font-medium text-gray-700">On an active call</span>
                </div>
                <input type="checkbox" checked={onCall} onChange={e => setOnCall(e.target.checked)} className="w-5 h-5 rounded text-blue-600" />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center gap-3">
                  <AlertTriangle className={`w-5 h-5 ${isCallFlagged ? 'text-red-500' : 'text-gray-400'}`} />
                  <span className="font-medium text-gray-700">Call is from Flagged/Spoofed #</span>
                </div>
                <input type="checkbox" checked={isCallFlagged} onChange={e => setIsCallFlagged(e.target.checked)} className="w-5 h-5 rounded text-blue-600" />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center gap-3">
                  <Clock className={`w-5 h-5 ${fdJustBroken ? 'text-amber-500' : 'text-gray-400'}`} />
                  <span className="font-medium text-gray-700">FD broken today</span>
                </div>
                <input type="checkbox" checked={fdJustBroken} onChange={e => setFdJustBroken(e.target.checked)} className="w-5 h-5 rounded text-blue-600" />
              </label>

              <div>
                <label className="flex justify-between text-sm font-medium text-gray-700 mb-2">
                  <span>Customer Age: {age}</span>
                </label>
                <input type="range" min="50" max="90" value={age} onChange={e => setAge(Number(e.target.value))} className="w-full" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Output & Trusted Person */}
        <div className="space-y-6">
          
          {/* Quick Scenarios */}
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => setScenario('normal')} className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-800 text-sm font-semibold rounded-lg transition-colors">Normal Payment</button>
            <button onClick={() => setScenario('digital_arrest')} className="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-800 text-sm font-semibold rounded-lg transition-colors">Digital Arrest Scam</button>
            <button onClick={() => setScenario('fd_break')} className="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 text-amber-800 text-sm font-semibold rounded-lg transition-colors">FD Break Transfer</button>
            <button onClick={() => setScenario('emergency')} className="px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-800 text-sm font-semibold rounded-lg transition-colors">Medical Emergency</button>
          </div>

          {/* Decision Display */}
          {decision && (
            <div className={`p-6 rounded-2xl shadow-sm border ${
              decision.action === 'ALLOW' ? 'bg-green-50 border-green-200' :
              decision.action === 'REJECT' ? 'bg-red-50 border-red-200' :
              decision.action === 'ESCALATE' ? 'bg-orange-50 border-orange-200' :
              'bg-amber-50 border-amber-200'
            }`}>
              <div className="flex items-start gap-4">
                {decision.action === 'ALLOW' && <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />}
                {decision.action === 'REJECT' && <ShieldAlert className="w-8 h-8 text-red-600 flex-shrink-0" />}
                {decision.action === 'HOLD' && <Clock className="w-8 h-8 text-amber-600 flex-shrink-0" />}
                {decision.action === 'ESCALATE' && <AlertTriangle className="w-8 h-8 text-orange-600 flex-shrink-0" />}
                
                <div>
                  <h3 className={`text-xl font-bold mb-2 ${
                    decision.action === 'ALLOW' ? 'text-green-800' :
                    decision.action === 'REJECT' ? 'text-red-800' :
                    decision.action === 'ESCALATE' ? 'text-orange-800' :
                    'text-amber-800'
                  }`}>
                    Action: {decision.action}
                  </h3>
                  <p className="text-gray-800 font-medium text-lg leading-snug">{decision.reason}</p>
                </div>
              </div>

              {isVerifying && (
                <div className="mt-4 pt-4 border-t border-amber-200 flex items-center gap-3 text-amber-800 font-medium animate-pulse">
                  <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                  Independent Bank Verification running...
                </div>
              )}

              {verificationResult && (
                <div className={`mt-4 pt-4 border-t ${verificationResult.verified ? 'border-green-200 text-green-700' : 'border-red-200 text-red-700'}`}>
                  <p className="font-bold flex items-center gap-2">
                    {verificationResult.verified ? <CheckCircle className="w-5 h-5"/> : <AlertTriangle className="w-5 h-5"/>}
                    {verificationResult.message}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Trusted Person View */}
          {decision?.action === 'HOLD' && payee === 'unlisted_emergency' && (
            <div className="bg-indigo-900 rounded-2xl p-6 text-white shadow-lg mt-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-indigo-500 text-xs font-bold px-3 py-1 rounded-bl-lg">TRUSTED PERSON VIEW</div>
              
              <div className="flex items-center gap-3 mb-4">
                <HeartPulse className="w-6 h-6 text-pink-400" />
                <h3 className="text-xl font-bold">Emergency Request</h3>
              </div>
              
              <p className="text-indigo-100 mb-6">
                Your parent is trying to send <strong className="text-white">₹{amount}</strong> to an unlisted payee. SafeVault held the payment to ensure they are safe.
              </p>

              {trustedPersonResponse ? (
                <div className={`p-4 rounded-xl font-bold ${trustedPersonResponse === 'APPROVED' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                  You {trustedPersonResponse.toLowerCase()} this transaction.
                </div>
              ) : (
                <div className="flex gap-3">
                  <button 
                    onClick={() => setTrustedPersonResponse('APPROVED')}
                    className="flex-1 bg-green-500 hover:bg-green-400 text-white font-bold py-3 rounded-xl transition-colors"
                  >
                    Approve Release
                  </button>
                  <button 
                    onClick={() => setTrustedPersonResponse('CANCELLED')}
                    className="flex-1 bg-red-500 hover:bg-red-400 text-white font-bold py-3 rounded-xl transition-colors"
                  >
                    Cancel Payment
                  </button>
                </div>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}

export default App;
