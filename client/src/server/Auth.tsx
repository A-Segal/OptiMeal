import axios from "axios";
import { base_url } from "../config";

export const loginUser = async (data: {
  username: string;
  password: string;
}) => {
  const res = await axios.post(`${base_url}/auth/login`, data);
  return res.data;
};