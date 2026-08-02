import axios from "axios"
import { base_url } from "../config"
import type {DistributionCenter}  from "../model/DistributionCenter"

export const addDistributionCenterSignUp = async (data:DistributionCenter) => {
    const res = await axios.post(`${ base_url}/distribution_center`,data)
    return res.data
}
export const getDistributionCenterSignUp = async () => {
    const res = await axios.get(`${ base_url}/distribution_center`)
    return res
}
export const updateDistributionCenter = async (id: number, data: { address: string }) => {
    const res = await axios.put(`${base_url}/distribution_center/${id}`, data)
    return res.data
}

