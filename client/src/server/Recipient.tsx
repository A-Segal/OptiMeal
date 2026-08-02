
import axios from "axios";
import { base_url } from "../config";
import type { Recipient } from "../model/Recipient";

export const addRecipient = async (data: Recipient) => {
  const res = await axios.post(`${base_url}/recipients`, data);
  return res.data;
};

export const updateRecipient = async (id: number, data: { address: string }) => {
  const res = await axios.put(`${base_url}/recipients/${id}`, data);
  return res.data;
};