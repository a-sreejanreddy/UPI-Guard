import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'development' ? "http://localhost:8000" : "");

if (!apiBaseUrl && import.meta.env.MODE !== 'development') {
  throw new Error("VITE_API_URL is required in production");
}

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
});

export default apiClient;
