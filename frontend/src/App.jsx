import { useState, useEffect } from 'react';
import { api } from './api';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [transRes, catRes] = await Promise.all([
        api.getTransactions(),
        api.getCategories()
      ]);
      setTransactions(transRes.data);
      setCategories(catRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await api.createTransaction({
        amount: parseFloat(amount),
        description,
        category_id: categoryId ? parseInt(categoryId) : null,
        date: new Date().toISOString(),
        type: 'expense'
      });
      
      const res = await api.getTransactions();
      setTransactions(res.data);
      
      setAmount('');
      setDescription('');
      setCategoryId('');
    } catch (error) {
      console.error('Error creating transaction:', error);
      alert('Error adding transaction. Make sure backend is running!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  const totalExpenses = transactions.reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            💰 SmartBudget
          </h1>
          <p className="text-gray-600">AI-Powered Personal Finance Tracker</p>
        </div>
        
        {/* Stats Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-red-500">
            <div className="text-sm text-gray-500 mb-1">Total Expenses</div>
            <div className="text-3xl font-bold text-red-500">
              ${totalExpenses.toFixed(2)}
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
            <div className="text-sm text-gray-500 mb-1">Transactions</div>
            <div className="text-3xl font-bold text-blue-500">
              {transactions.length}
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
            <div className="text-sm text-gray-500 mb-1">Avg per Transaction</div>
            <div className="text-3xl font-bold text-green-500">
              ${transactions.length > 0 ? (totalExpenses / transactions.length).toFixed(2) : '0.00'}
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Add Transaction Form */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-gray-800">
              ➕ Add Transaction
            </h2>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full border-2 border-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder="50.00"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full border-2 border-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder="Lunch at Starbucks"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full border-2 border-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                >
                  <option value="">🤖 Auto-categorize with AI</option>
                  {categories.filter(c => c.type === 'expense').map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Leave blank to let AI categorize automatically
                </p>
              </div>
              
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-blue-600 hover:to-indigo-700 font-medium transition shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
              >
                Add Transaction
              </button>
            </form>
          </div>

          {/* Transactions List */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-6 text-gray-800">
              📊 Recent Transactions
            </h2>
            
            {transactions.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🚀</div>
                <p className="text-gray-500 text-lg">No transactions yet</p>
                <p className="text-gray-400 text-sm mt-2">
                  Add your first transaction to get started!
                </p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {transactions.slice(0).reverse().map(t => (
                  <div 
                    key={t.id} 
                    className="flex justify-between items-center p-4 border-2 border-gray-100 rounded-lg hover:border-blue-200 hover:shadow-md transition"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-gray-800">
                        {t.description}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">
                        <span className="inline-block mr-2">
                          {categories.find(c => c.id === t.category_id)?.icon || '📝'}
                        </span>
                        {t.category_name || 'Uncategorized'} • 
                        {' '}{new Date(t.date).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="text-xl font-bold text-red-500 ml-4">
                      -${t.amount.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;