import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = {
  getTransactions: () => axios.get(`${API_URL}/transactions?user_id=1`),
  createTransaction: (data) => axios.post(`${API_URL}/transactions`, { 
    ...data, 
    user_id: 1 
  }),
  deleteTransaction: (id) => axios.delete(`${API_URL}/transactions/${id}`),
  getCategories: () => axios.get(`${API_URL}/categories`),
  getSpendingByCategory: () => axios.get(`${API_URL}/analytics/spending-by-category?user_id=1&days=30`),
  getMonthlyTrend: () => axios.get(`${API_URL}/analytics/monthly-trend?user_id=1&months=6`),
};