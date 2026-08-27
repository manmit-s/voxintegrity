import { useEffect, useState } from 'react'
import { getHistory } from '../services/api'

export default function History() {
  const [items, setItems] = useState([])
  useEffect(() => {
    getHistory().then(res => setItems(res.data.history)).catch(()=>{})
  }, [])
  return <div><h2>History</h2><pre>{JSON.stringify(items, null, 2)}</pre></div>
}
