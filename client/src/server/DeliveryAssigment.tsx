import axios from "axios"
import { base_url } from "../config"
import type {DeliveryAssignment}  from "../model/DeliveryAssignment"

export const addDeliveryAssignment = async (data:DeliveryAssignment) => {
    const res = await axios.post(`${ base_url}/delivery_assignment`,data)    
    return res
}
export const getDeliveryAssignments = async () => {
    const res = await axios.get(`${ base_url}/delivery_assignment`)
    return res
}
