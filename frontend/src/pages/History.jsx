import React, { useEffect, useState } from 'react'
import { getHistory } from '../services/api'

export default function History() {
  const [items, setItems] = useState([{ id: 'VK-26-0906-0012', file: 'field_sample_07.wav', date: '06 SEP 2026 / 13:48', verdict: 'AUTHENTIC', confidence: '96.8%' }, { id: 'VK-26-0905-0094', file: 'speaker_check.m4a', date: '05 SEP 2026 / 18:21', verdict: 'AUTHENTIC', confidence: '94.1%' }, { id: 'VK-26-0904-0041', file: 'unknown_input.mp3', date: '04 SEP 2026 / 09:06', verdict: 'REVIEW', confidence: '61.3%' }])
  useEffect(() => {
    getHistory().then(res => { if (res.data?.history?.length) setItems(res.data.history) }).catch(() => {})
  }, [])
  return <section className="console-page history-page"><div className="page-heading"><div><p className="eyebrow">ARCHIVE / VERIFIED SESSIONS</p><h1>Session History</h1></div><div className="session-badge"><span>RECORDS</span><strong>{String(items.length).padStart(2, '0')}</strong></div></div><div className="panel table-panel"><div className="panel-label"><span>RECENT ANALYSIS RUNS</span><span>RETENTION: 30 DAYS</span></div><div className="history-table"><div className="history-head"><span>SESSION</span><span>INPUT FILE</span><span>DATE / TIME</span><span>VERDICT</span><span>CONFIDENCE</span></div>{items.map(item => <div className="history-row" key={item.id}><strong>{item.id}</strong><span>{item.file}</span><span>{item.date}</span><b className={item.verdict === 'REVIEW' ? 'review' : 'good'}>{item.verdict}</b><strong>{item.confidence}</strong></div>)}</div></div></section>
}
