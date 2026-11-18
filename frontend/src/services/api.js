import axios from "axios";
const API = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000" });
API.interceptors.request.use((config) => { const token = localStorage.getItem("ff_token"); if (token) config.headers.Authorization = `Bearer ${token}`; return config; });
export const auth = { register: (data) => API.post('/register', data), login: (data) => API.post('/login', data), adminLogin: (data) => API.post('/admin/login', data), me: () => API.get('/me') };
export default API;
